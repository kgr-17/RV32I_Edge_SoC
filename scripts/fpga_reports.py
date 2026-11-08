"""Parse actual Vivado reports conservatively; no fabricated signoff defaults."""
import math
import re


def finite(value):
    result=float(value)
    if not math.isfinite(result):raise ValueError('FPGA_NONFINITE_REPORT_NUMBER')
    return result


def report_header(text,state):
    for expression in (r'Tool Version\s*:\s*Vivado v\.2025\.2 .*Build 6299465',
                       r'^\|[ \t]*Design[ \t]*:[ \t]*basys3_top[ \t]*$',
                       r'^\|[ \t]*Design State[ \t]*:[ \t]*'+state+r'[ \t]*$'):
        if not re.search(expression,text,re.M):raise ValueError('FPGA_REPORT_HEADER '+expression)
    if not re.search(r'^\|[ \t]*Device[ \t]*:[ \t]*(?:xc7a35tcpg236-1|7a35t-cpg236)[ \t]*$',text,re.M):
        raise ValueError('FPGA_REPORT_DEVICE')
    if '7a35t-cpg236' in text and not re.search(r'^\|[ \t]*Speed File[ \t]*:[ \t]*-1\b',text,re.M):
        raise ValueError('FPGA_REPORT_SPEED_GRADE')


TIMING_CHECKS={'no_clock','constant_clock','pulse_width_clock','unconstrained_internal_endpoints',
    'no_input_delay','no_output_delay','multiple_clock','generated_clocks','loops',
    'partial_input_delay','partial_output_delay','latch_loops'}


def timing(text,state='Routed',require_closure=True):
    report_header(text,state)
    if 'report_unconstrained' not in text or not re.search(r'Ignore I/O Paths\s*:\s*No',text):
        raise ValueError('FPGA_TIMING_PATH_SCOPE')
    matches=re.findall(r'^\d+\. checking ([a-z_]+) \((\d+)\)\s*$',text,re.M)
    checks={}
    for name,count in matches:
        count=int(count)
        if name in checks and checks[name]!=count:raise ValueError('FPGA_CONTRADICTORY_TIMING_CHECK '+name)
        checks[name]=count
    if set(checks)!=TIMING_CHECKS:raise ValueError('FPGA_TIMING_CHECK_INVENTORY')
    for name,count in checks.items():
        if name not in {'no_input_delay','no_output_delay'} and count:
            raise ValueError('FPGA_UNCONSTRAINED_OR_INVALID_INTERNAL_PATH '+name)
    if (checks['no_input_delay'],checks['no_output_delay'])!=(18,17):
        raise ValueError('FPGA_EXTERNAL_PORT_INVENTORY')
    if not re.search(r'^sys_clk\s+\{0\.000 5\.000\}\s+10\.000\s+100\.000\s*$',text,re.M):
        raise ValueError('FPGA_REPORT_CLOCK')
    marker='| Design Timing Summary'
    if text.count(marker)!=1:raise ValueError('FPGA_TIMING_SUMMARY_COUNT')
    section=text.split(marker)[1].split('| Clock Summary')[0]
    rows=[line.split() for line in section.splitlines() if len(line.split())==12 and re.match(r'^\s*-?\d',line)]
    if len(rows)!=1:raise ValueError('FPGA_TIMING_SUMMARY_SHAPE')
    values=list(map(finite,rows[0]));result={}
    for offset,prefix in ((0,'setup'),(4,'hold'),(8,'pulse_width')):
        slack,total,failing,endpoints=values[offset:offset+4]
        if (failing!=int(failing) or endpoints!=int(endpoints) or endpoints<=0 or
            failing<0 or failing>endpoints or total>0):raise ValueError('FPGA_TIMING_ENDPOINT_COUNTS')
        if require_closure and (slack<0 or total!=0 or failing!=0):
            raise ValueError('FPGA_ROUTED_TIMING_FAILED '+prefix+' slack='+str(slack))
        result[prefix]={'worst_slack_ns':slack,'total_negative_slack_ns':total,
            'failing_endpoints':int(failing),'endpoints':int(endpoints)}
    result.update(checks=checks,clock_period_ns=10.0,external_io_delays='UNSPECIFIED:18 async inputs/17 non-synchronous outputs; no off-chip timing closure claim')
    return result


def utilization(text,state):
    report_header(text,state)
    expected={'Slice LUTs':20800,'Slice Registers':41600,'Block RAM Tile':50,'Bonded IOB':106}
    result={}
    for line in text.splitlines():
        if not line.startswith('|'):continue
        fields=[f.strip().rstrip('*') for f in line.split('|')[1:-1]]
        if len(fields)==6 and fields[0] in expected:
            name=fields[0]
            used,fixed,prohibited,available,percent=map(finite,fields[1:])
            if available!=expected[name] or not 0<=used<=available or fixed<0 or prohibited<0:
                raise ValueError('FPGA_RESOURCE_CAPACITY '+name)
            if abs(percent-used*100/available)>0.011:raise ValueError('FPGA_RESOURCE_PERCENT')
            row={'used':used,'available':int(available),'percent':percent}
            # Routed reports repeat the same register count in Slice Logic
            # Distribution. Require agreement with the earlier summary row.
            if name in result and result[name]!=row:raise ValueError('FPGA_CONTRADICTORY_RESOURCE_ROW')
            result[name]=row
        if fields and fields[0]=='Register as Latch' and int(fields[1])!=0:raise ValueError('FPGA_LATCH_REPORTED')
    if set(result)!=set(expected) or result['Block RAM Tile']['used']!=32 or result['Bonded IOB']['used']!=36:
        raise ValueError('FPGA_RESOURCE_OR_MEMORY_INVENTORY')
    return result


def bitstream(data):
    position=0
    def take(n):
        nonlocal position
        value=data[position:position+n];position+=n
        if len(value)!=n:raise ValueError('FPGA_TRUNCATED_BITSTREAM')
        return value
    def length(n):return int.from_bytes(take(n),'big')
    if take(length(2))!=bytes.fromhex('0ff00ff00ff00ff000') or length(2)!=1:
        raise ValueError('FPGA_BITSTREAM_MAGIC')
    fields={}
    for key in (b'a',b'b',b'c',b'd'):
        if take(1)!=key:raise ValueError('FPGA_BITSTREAM_FIELD_ORDER')
        value=take(length(2))
        if not value.endswith(b'\0'):raise ValueError('FPGA_BITSTREAM_FIELD_TERMINATOR')
        fields[key.decode()]=value[:-1].decode('ascii')
    if take(1)!=b'e':raise ValueError('FPGA_BITSTREAM_PAYLOAD_FIELD')
    payload=take(length(4))
    if position!=len(data) or len(payload)<100000 or b'\xaa\x99\x55\x66' not in payload[:512]:
        raise ValueError('FPGA_BITSTREAM_PAYLOAD')
    if fields['b']!='7a35tcpg236':raise ValueError('FPGA_BITSTREAM_PART')
    return {'design':fields['a'],'part':fields['b'],'date':fields['c'],'time':fields['d'],'payload_bytes':len(payload)}


def physical_inventory(text,pins):
    rows=[line.split('\t') for line in text.splitlines()]
    scalars={r[0]:r[1] for r in rows if len(r)==2}
    if set(scalars)!={'part','ports','clocks','period','async_regs','clocked_reset_copies'}:
        raise ValueError('FPGA_PHYSICAL_INVENTORY_SHAPE')
    if (scalars['part']!='xc7a35tcpg236-1' or scalars['ports']!='36' or scalars['clocks']!='1' or
        finite(scalars['period'])!=10 or scalars['async_regs']!='36' or int(scalars['clocked_reset_copies'])<1):
        raise ValueError('FPGA_PHYSICAL_CONTRACT')
    observed={}
    for row in rows:
        if row[0]=='port':
            if len(row)!=5 or row[1] in observed:raise ValueError('FPGA_PHYSICAL_PORT_ROW')
            observed[row[1]]=[row[3],row[2]]
            if row[4]!='LVCMOS33':raise ValueError('FPGA_PHYSICAL_IOSTANDARD')
    if observed!=pins['pins']:raise ValueError('FPGA_PHYSICAL_PIN_BINDING')
    expected={(f'soc/fabric/gpio_unit/inputs/meta_q_reg[{i}]',f'soc/fabric/gpio_unit/inputs/sync_q_reg[{i}]') for i in range(16)}
    expected|={('soc/fabric/uart/receiver/rx_meta_q_reg','soc/fabric/uart/receiver/rx_sync_q_reg'),
        ('reset_boundary/g_sync.release_q_reg[0]','reset_boundary/g_sync.release_q_reg[1]')}
    chains=[r for r in rows if r[0]=='chain']
    if len(chains)!=18 or any(len(r)!=6 or r[3:]!=['1','1','1'] for r in chains) or {(r[1],r[2]) for r in chains}!=expected:
        raise ValueError('FPGA_PHYSICAL_SYNCHRONIZER_INVENTORY')
    if len(rows)!=6+36+18:raise ValueError('FPGA_UNEXPECTED_INVENTORY_ROWS')
    return {'ports':36,'clock_period_ns':10,'async_chains':18,'async_registers':36,'clocked_reset_copies':int(scalars['clocked_reset_copies'])}


def routed_reports(folder):
    """Decode reports, retaining negative timing values without claiming PASS."""
    import harness
    def text(name):
        value=(folder/name).read_text(encoding='utf-8')
        if len(value)<50:raise ValueError('FPGA_EMPTY_REPORT '+name)
        return value
    result={'timing':timing(text('routed_timing.rpt'),require_closure=False),
        'utilization':utilization(text('routed_utilization.rpt'),'Routed')}
    clocks=text('routed_clocks.rpt');report_header(clocks,'Routed')
    if len(re.findall(r'^sys_clk\s+10\.000\s+\{0\.000 5\.000\}\s+P\s+\{clk\}\s*$',clocks,re.M))!=1:
        raise ValueError('FPGA_CLOCK_REPORT_CONTENT')
    interaction=text('routed_clock_interaction.rpt');report_header(interaction,'Routed')
    if not re.search(r'^sys_clk\s+sys_clk\s+rise - rise.*Clean\s+Timed\s*$',interaction,re.M):raise ValueError('FPGA_CLOCK_INTERACTION')
    cdc=text('routed_cdc.rpt');report_header(cdc,'Routed')
    if '-no_waiver' not in cdc or 'All paths are Safely Timed.' not in cdc:raise ValueError('FPGA_CDC_FINDING')
    drc=text('routed_drc.rpt');report_header(drc,'Fully Routed')
    if not (re.search(r'Checks found:\s*0\b',drc) or 'No violations found.' in drc or 'No DRC violations found.' in drc):
        raise ValueError('FPGA_DRC_FINDING')
    if re.search(r'(?m)^\S+#\d+\s+(?:Warning|Critical Warning|Error)',drc):raise ValueError('FPGA_DRC_DETAIL')
    # report_route_status emits no tool header in pinned Vivado 2025.2.
    # Its native job/byte hashes supply provenance; validate the exact body.
    route=text('routed_route_status.rpt')
    if not route.startswith('Design Route Status\n'):raise ValueError('FPGA_ROUTE_STATUS_HEADER')
    net_rows=re.findall(r'# of ([a-z ]+)\.+\s*:\s*(\d+)\s*:',route)
    nets={name:int(value) for name,value in net_rows}
    if (len(net_rows)!=6 or set(nets)!={'logical nets','nets not needing routing','internally routed nets',
        'routable nets','fully routed nets','nets with routing errors'} or nets['nets with routing errors']!=0 or
        nets['fully routed nets']!=nets['routable nets'] or nets['routable nets']<=0 or
        nets['logical nets']!=nets['nets not needing routing']+nets['routable nets'] or
        not 0<=nets['internally routed nets']<=nets['nets not needing routing']):raise ValueError('FPGA_ROUTE_STATUS')
    result['route_status']=nets
    effective=text('effective_constraints.xdc')
    if re.search(r'(?m)^\s*(?:set_false_path|set_multicycle_path|set_max_delay|set_min_delay)\b',effective):
        raise ValueError('FPGA_UNREVIEWED_TIMING_EXCEPTION')
    inventory=text('physical_inventory.tsv')
    result['physical_inventory']=physical_inventory(inventory,harness.read(harness.inside('config/basys3_pins.json')))
    power=text('routed_power.rpt');report_header(power,'routed')
    def field(name):
        rows=re.findall(r'^\|\s*'+re.escape(name)+r'\s*\|\s*([^|]+)\|\s*$',power,re.M)
        if len(rows)!=1:raise ValueError('FPGA_POWER_FIELD '+name)
        return rows[0].strip()
    total,dynamic,static=(finite(field(n)) for n in ('Total On-Chip Power (W)','Dynamic (W)','Device Static (W)'))
    if min(total,dynamic,static)<0 or abs(total-dynamic-static)>0.002:raise ValueError('FPGA_POWER_TOTALS')
    confidence=field('Confidence Level')
    if confidence not in ('Low','Medium','High') or field('Simulation Activity File')!='---':raise ValueError('FPGA_POWER_ASSUMPTION')
    activity=text('routed_activity.rpt')
    if 'btnC' not in activity:raise ValueError('FPGA_POWER_ACTIVITY_REPORT')
    result['power']={'total_w':total,'dynamic_w':dynamic,'static_w':static,'confidence':confidence,
        'activity':'Vectorless, resets deasserted; defaults for unspecified switching; no simulation activity file or measurement'}
    result['cdc_scope']='One-clock native CDC report plus18 structural synchronizer chains; no metastability proof or off-chip clock/timing specification'
    return result


def validate_complete(folder):
    """Acceptance requires closed timing and a real, correctly targeted image."""
    result=routed_reports(folder)
    result['timing']=timing((folder/'routed_timing.rpt').read_text(encoding='utf-8'))
    result['bitstream']=bitstream((folder/'design.bit').read_bytes())
    return result
