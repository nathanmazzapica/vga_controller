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
wire [2:0] pixel_x = h_count[2:0];
wire [2:0] pixel_y = v_count[2:0];

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


wire [12:0] vram_addr;
text_renderer u_text_renderer (
    .h_count(h_count),
    .v_count(v_count),
    .index(vram_addr)
);

wire [7:0] char_code;
vram u_vram(
    .clk(clk),
    .write_en(),
    .data_in(),
    .write_addr(),
    .read_addr(vram_addr),
    .data_out(char_code)
);

wire [63:0] glyph;
font_rom u_font_rom(
    .clk(clk),
    .char_code(char_code),
    .glyph(glyph)
);

vga_color color (
    .clk(clk),
    .h_count(h_count),
    .v_count(v_count),
    .pixel_x(pixel_x),
    .pixel_y(pixel_y),
    .glyph(glyph),
    .active_video(active_video),
    .offset_x(offset_x),
    .offset_y(offset_y),
    .r(r),
    .g(g),
    .b(b)
);
endmodule
