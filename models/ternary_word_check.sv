// Checks a 32-bit SRAM word holding 16 ternary weights for invalid codes.
//
// Encoding (spec/sram_spec.md, same as the flagship PEs):
//   00 -> 0    01 -> +1    10 -> -1    11 -> INVALID (a stored bit flipped)
//
// Purely combinational. Put it on an SRAM read port and every word that comes
// out is checked for free. Feed `n_invalid` into an error counter and you have
// a per-bank bit-flip (radiation) monitor.
module ternary_word_check #(
    parameter int LANES = 16
) (
    input  logic [2*LANES-1:0]       word,
    output logic [LANES-1:0]         invalid,    // one bit per lane
    output logic                     any_invalid,
    output logic [$clog2(LANES+1)-1:0] n_invalid // how many lanes were 11
);
    always_comb begin
        n_invalid = '0;
        for (int i = 0; i < LANES; i++) begin
            invalid[i] = (word[2*i +: 2] == 2'b11);
            n_invalid  = n_invalid + invalid[i];
        end
        any_invalid = |invalid;
    end
endmodule
