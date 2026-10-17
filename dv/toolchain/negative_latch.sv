// Intentional latch fixture to prove the lint gate rejects inferred storage.
`default_nettype none
module negative_latch (
    input wire logic gate_i,
    input wire logic [7:0] data_i,
    output logic [7:0] data_o
);
    always_latch begin
        if (gate_i) data_o <= data_i;
    end
endmodule
`default_nettype wire
