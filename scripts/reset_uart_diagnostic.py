"""Reproduce a reset-chatter mechanism without changing RTL or physical gates."""
import datetime as dt
import json
import shutil
import sys
import harness,hardware,rtl_checks,soc_checks
sys.path.insert(0,str(harness.inside('dv/integration')))
from soc_model import decode_uart


def main():
    c=rtl_checks.Checks('reset-uart-diagnostic',task='T032',scope='Simulation of unchanged actual board/IRQ image with ideal and representative bouncing button release; no new bitstream/physical acceptance')
    code=1
    try:
        config=harness.read(harness.inside('config/fpga_build.json'))
        names=config['rtl_sources']+config['memory_files']+['dv/integration/tb_reset_uart_diagnostic.sv','scripts/reset_uart_diagnostic.py','dv/integration/soc_model.py']
        c.result['source_sha256']={n:hardware.sha(harness.inside(n)) for n in names}
        c.versions(rtl_checks.load_manifest())
        work=c.base/'simulation';work.mkdir()
        shutil.copyfile(harness.inside('fpga/basys3/irq_boot.mem'),work/'irq_boot.mem')
        soc_checks.compile_design(c,work,config['rtl_sources'],['dv/integration/tb_reset_uart_diagnostic.sv'])
        soc_checks.elaborate(c,work,'tb_reset_uart_diagnostic','reset_uart')
        results=[]
        for mode in (0,1):
            trace=work/('mode%d.trace'%mode)
            r=soc_checks.simulate(c,work,'reset_uart','mode%d'%mode,['MODE=%d'%mode,'TRACE='+str(trace)],'/tb_reset_uart_diagnostic/clk /tb_reset_uart_diagnostic/button /tb_reset_uart_diagnostic/board/rst_s /tb_reset_uart_diagnostic/tx',60)
            prefix='RESET_UART_DIAGNOSTIC_COMPLETE mode=%d rows='%mode
            c.require(rtl_checks.successful(r) and sum(line.startswith(prefix) for line in r['stdout'].splitlines())==1,'Actual complete reset diagnostic mode%d'%mode,r)
            rows=[[int(w) for w in line.split()] for line in trace.read_text(encoding='ascii').splitlines()]
            c.require(rows and all(len(row)==4 and row[0]==n and all(bit in (0,1) for bit in row[1:]) for n,row in enumerate(rows)),'Complete deterministic TX/reset trace mode%d'%mode)
            levels=[row[3] for row in rows]
            if mode==0:
                decoded=decode_uart(levels,868)
                c.require(decoded==b'IRQ PASS\r\n','Ideal actual board boot exact IRQ PASS')
                results.append({'mode':mode,'rows':len(rows),'decoded_hex':decoded.hex()})
            else:
                try:decode_uart(levels,868)
                except ValueError as exc:
                    diagnostic=str(exc);c.require(diagnostic in ('SOC_UART_FRAMING','SOC_UART_BIT_WIDTH'),'Unchanged strict decoder rejects reset-interrupted UART')
                else:raise ValueError('Reset chatter unexpectedly produced a clean full trace')
                last_reset=max(n for n,row in enumerate(rows) if row[2])
                decoded=decode_uart(levels[last_reset+1:],868)
                c.require(decoded==b'IRQ PASS\r\n','Actual firmware succeeds after final simulated reset stabilizes')
                results.append({'mode':mode,'rows':len(rows),'whole_trace_rejection':diagnostic,'last_internal_reset_cycle':last_reset,'stable_suffix_hex':decoded.hex(),
                    'limitation':'Suffix separation is simulation diagnosis only; physical capture gate remains unchanged and no bytes are discarded there'})
        c.result['results']=results
        c.require(all(hardware.sha(harness.inside(n))==d for n,d in c.result['source_sha256'].items()),'Diagnostic inputs unchanged')
        c.result['status']='PASS';code=0
    except (ValueError,RuntimeError,OSError,KeyError,harness.Stop) as exc:c.result.update(status='FAIL',error=str(exc))
    c.result['artifacts']={hardware.rel(p):hardware.sha(p) for p in c.base.rglob('*') if p.is_file()}
    c.result['finished_utc']=dt.datetime.now(dt.timezone.utc).isoformat();c.save()
    print(json.dumps({'status':c.result['status'],'receipt':hardware.rel(c.path),'results':c.result.get('results'),'error':c.result.get('error')}));return code


if __name__=='__main__':sys.exit(main())
