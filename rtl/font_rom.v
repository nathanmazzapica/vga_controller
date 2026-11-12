`timescale 1ns / 1ps
module font_rom(
    input wire clk,
    input wire [7:0] char_code,
    output reg [63:0] glyph
);

reg [63:0] glyphs [0:255];

initial begin
    $readmemh("font_ascii_8x8.mem", glyphs);
end

always @(posedge clk) begin
    glyph <= glyphs[char_code];
end

endmodule;
