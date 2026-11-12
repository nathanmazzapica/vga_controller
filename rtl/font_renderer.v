`timescale 1ns / 1ps
module font_renderer (
    input wire clk,
    input   wire [2:0] pixel_x, pixel_y,
    input   wire [63:0] glyph,
    output  wire foreground,
    output wire chk
);

reg [2:0] pixel_x_d1, pixel_x_d2;
reg [2:0] pixel_y_d1, pixel_y_d2;

always @(posedge clk) begin
    pixel_x_d1 <= pixel_x;
    pixel_x_d2 <= pixel_x_d1;

    pixel_y_d1 <= pixel_y;
    pixel_y_d2 <= pixel_y_d1;
end

wire [5:0] pixel = {pixel_y_d2, pixel_x_d2};
assign foreground = glyph[6'd63 - pixel];
assign chk = pixel_x_d2[0] ^ pixel_y_d2[0];

endmodule
