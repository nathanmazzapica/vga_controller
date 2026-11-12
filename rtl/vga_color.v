module vga_color#(
    parameter BOX_SIZE = 8
)(
    input wire clk,
    input wire [9:0] h_count,
    input wire [9:0] v_count,
    input wire [2:0] pixel_x, pixel_y,
    input wire [63:0] glyph,
    input wire active_video,
    input wire [9:0] offset_x, offset_y, 
    output reg [3:0] r,g,b
);

localparam [11:0] PURPLE = 12'hF0F;
localparam [11:0] RED = 12'hF00;
localparam [11:0] GREEN = 12'h0F0;
localparam [11:0] BLUE = 12'h00F;
localparam [11:0] ORANGE = 12'hFA5;
localparam [11:0] BLACK = 12'h000;
localparam [11:0] WHITE = 12'hFFF;

wire foreground;

font_renderer u_font_renderer (
    .clk(clk),
    .pixel_x(pixel_x),
    .pixel_y(pixel_y),
    .glyph(glyph),
    .foreground(foreground)
);


wire in_box = (h_count >= offset_x) && (h_count < offset_x + BOX_SIZE) &&
                (v_count >= offset_y) && (v_count < offset_y + BOX_SIZE);

always @(*) begin
    {r, g, b} = BLACK;
    if (in_box)
        {r, g, b} = ORANGE;

    if (active_video) begin
        if (foreground)
            {r, g, b} = WHITE;

    end
end
endmodule
