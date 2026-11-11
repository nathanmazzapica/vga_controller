module vga_controller(
    input wire clk,
    input wire rst,
    input wire [9:0] offset_x, offset_y,

    output wire hsync,
    output wire vsync,

    output wire [3:0] r,g,b,
    output wire active_video,
    output wire frame_start
);

wire [9:0] h_count, v_count;

vga_timing timing (
    .clk(clk),
    .rst(rst),
    .hsync(hsync),
    .vsync(vsync),
    .h_count(h_count),
    .v_count(v_count),
    .active_video(active_video),
    .frame_start(frame_start)
);

vga_color color (
    .h_count(h_count),
    .v_count(v_count),
    .active_video(active_video),
    .offset_x(offset_x),
    .offset_y(offset_y),
    .r(r),
    .g(g),
    .b(b)
);
endmodule
