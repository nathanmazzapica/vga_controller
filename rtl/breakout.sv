`timescale 1ns/1ps
module breakout(
    input logic clk,
    input logic btnC,
    input logic btnU, btnR, btnL, btnD,
    output [3:0] vgaRed,
    output [3:0] vgaBlue,
    output [3:0] vgaGreen,
    output Hsync, Vsync
);

wire pix_clk, locked;

wire [3:0] mov = {btnU, btnR, btnL, btnD};


clk_wiz_0 u_clk(
    .clk_in1(clk),
    .reset(btnC),
    .clk_out1(pix_clk),
    .locked(locked)
);

logic active_video;
logic frame_start;

logic rst = btnC | ~locked;

logic [9:0] h_count;
logic [9:0] v_count;

vga_timing u_vga_timing (
    .clk(clk),
    .rst(rst),
    .hsync(Hsync),
    .vsync(Vsync),
    .active_video(active_video),
    .frame_start(frame_start),
    .h_count(h_count),
    .v_count(v_count)
);

logic [27:0] brick_occupancy;
breakout_brick_occupancy u_brick_occupancy(
    .clk(clk),
    .rst(rst),
    .brick_addr(),
    .brick_occupancy(brick_occupancy)
);


logic draw_wall;
logic draw_bg;
logic draw_brick;
breakout_tilemap u_tilemap(
    .h_count(h_count),
    .v_count(v_count),
    .brick_occupancy(brick_occupancy),
    .draw_wall(draw_wall),
    .draw_bg(draw_bg),
    .draw_brick(draw_brick)
);

breakout_color u_color(
    .active_video(active_video),
    .draw_wall(draw_wall),
    .draw_bg(draw_bg),
    .draw_brick(draw_brick),
    .r(vgaRed),
    .g(vgaGreen),
    .b(vgaBlue)
);



endmodule
