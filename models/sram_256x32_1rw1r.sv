// Behavioral (simulation-only) model of the 1 KB SRAM in spec/sram_spec.md.
//
// 256 words x 32 bits, port 0 = read/write with byte mask, port 1 = read-only.
// Port names match OpenRAM's sky130_sram_1kbyte_1rw1r_32x256_8, so the flagship
// can swap this file for the real macro without changing any wiring.
//
// This is NOT synthesizable into a real memory. It's a stand-in so the flagship
// can simulate against the SRAM today, before the real block exists.
module sram_256x32_1rw1r #(
    parameter int ADDR_W = 8,
    parameter int DATA_W = 32,
    parameter int DEPTH  = 1 << ADDR_W
) (
`ifdef USE_POWER_PINS
    inout  wire                vccd1,
    inout  wire                vssd1,
`endif
    // Port 0: read/write
    input  logic               clk0,
    input  logic               csb0,    // active low
    input  logic               web0,    // active low: 0 = write, 1 = read
    input  logic [DATA_W/8-1:0] wmask0, // byte enables
    input  logic [ADDR_W-1:0]  addr0,
    input  logic [DATA_W-1:0]  din0,
    output logic [DATA_W-1:0]  dout0,
    // Port 1: read-only
    input  logic               clk1,
    input  logic               csb1,    // active low
    input  logic [ADDR_W-1:0]  addr1,
    output logic [DATA_W-1:0]  dout1
);
    logic [DATA_W-1:0] mem [DEPTH];

    // Port 0
    always_ff @(posedge clk0) begin
        if (!csb0) begin
            if (!web0) begin
                for (int b = 0; b < DATA_W / 8; b++)
                    if (wmask0[b]) mem[addr0][8*b +: 8] <= din0[8*b +: 8];
            end else begin
                dout0 <= mem[addr0];
            end
        end
    end

    // Port 1. Reading the address port 0 is writing in the same cycle returns
    // the OLD data here, but the spec says that case is undefined: don't rely on it.
    always_ff @(posedge clk1) begin
        if (!csb1) dout1 <= mem[addr1];
    end
endmodule
