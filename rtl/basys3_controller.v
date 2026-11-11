`timescale 1ns/1ps
module basys3_controller(
    input wire clk,
    input wire btnC,
    output [3:0] vgaRed,
    output [3:0] vgaBlue,
    output [3:0] vgaGreen,
    output Hsync, Vsync
);

wire pix_clk, locked;


clk_wiz_0 u_clk(
    .clk_in1(clk),
    .reset(btnC),
    .clk_out1(pix_clk),
    .locked(locked)
);

wire frame_start;

box_mover u_box_mover (
    .clk(clk),
    .rst(rst),
    .frame_start(frame_start),
    .offset_x(box_x),
    .offset_y(box_y)
);



wire rst = btnC | ~locked;

wire [9:0] box_x, box_y;
vga_controller u_vga (
    .clk(pix_clk),
    .rst(rst),
    .offset_x(box_x),
    .offset_y(box_y),
    .hsync(Hsync),
    .vsync(Vsync),
    .r(vgaRed),
    .g(vgaGreen),
    .b(vgaBlue),
    .active_video(),
    .frame_start(frame_start)
);

assign box_x = 10'd100;
assign box_y = 10'd100;

endmodule
