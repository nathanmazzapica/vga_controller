`timescale 1ns / 1ps
module font_rom(
    input wire clk,
    input wire [7:0] char_code,
    output reg [63:0] glyph
);

reg [63:0] glyphs [0:255];

initial begin
    glyphs [8'd32] = 64'b0;
    glyphs[8'd65] = {
        8'b00111100_,
        8'b01100110_,
        8'b11000011_,
        8'b11000011_,
        8'b11111111_,
        8'b11000011_,
        8'b11000011_,
        8'b00000000
        };
    glyphs[66] = {
        8'b11111100,
        8'b11000110,
        8'b11000110,
        8'b11111100,
        8'b11000110,
        8'b11000110,
        8'b11111100,
        8'b00000000
    };

    // C (ASCII 67)
    glyphs[67] = {
        8'b00111100,
        8'b01100110,
        8'b11000000,
        8'b11000000,
        8'b11000000,
        8'b01100110,
        8'b00111100,
        8'b00000000
    };

end

always @(posedge clk) begin
    glyph <= glyphs[char_code];
end

endmodule;
