module vga_controller(
    input wire clk,
    input wire rst,
    input wire [9:0] offset_x, offset_y,

    output wire hsync_out,
    output wire vsync_out,

    output wire [3:0] r,g,b,
    output wire active_out,
    output wire frame_start_out
);

wire [9:0] h_count, v_count;
wire [2:0] pixel_x = h_count[2:0];
wire [2:0] pixel_y = v_count[2:0];

reg [1:0] hsync_delay;
reg [1:0] vsync_delay;
reg [1:0] active_delay;
reg [1:0] frame_start_delay;


reg [9:0] h_d1, h_d2;
reg [9:0] v_d1, v_d2;

wire hsync;
wire vsync;
wire active_video;
wire frame_start;

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
    .h_count(h_d2),
    .v_count(v_d2),
    .pixel_x(pixel_x),
    .pixel_y(pixel_y),
    .glyph(glyph),
    .active_video(active_out),
    .offset_x(offset_x),
    .offset_y(offset_y),
    .r(r),
    .g(g),
    .b(b)
);

always @(posedge clk) begin
    if (rst) begin
        // Syncs are active-low: idle high. Keep active/frame_start low so
        // the (0,0) state held during reset doesn't leak out as extra pixels.
        hsync_delay <= 2'b11;
        vsync_delay <= 2'b11;
        active_delay <= 2'b00;
        frame_start_delay <= 2'b00;
    end
    else begin
        hsync_delay <= {hsync_delay[0], hsync};
        vsync_delay <= {vsync_delay[0], vsync};
        active_delay <= {active_delay[0], active_video};
        frame_start_delay <= {frame_start_delay[0], frame_start};
    end

    h_d1 <= h_count;
    h_d2 <= h_d1;

    v_d1 <= v_count;
    v_d2 <= v_d1;
end

assign hsync_out = hsync_delay[1];
assign vsync_out = vsync_delay[1];
assign active_out = active_delay[1];
assign frame_start_out = frame_start_delay[1];


endmodule
