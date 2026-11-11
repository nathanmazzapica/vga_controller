module vga_color#(
    parameter BOX_SIZE = 32
)(
    input wire [9:0] h_count,
    input wire [9:0] v_count,
    input wire active_video,
    input wire [9:0] offset_x, offset_y,
    output reg [3:0] r,g,b
);

integer sq_width = 32;
integer sq_height = 32;

localparam [11:0] PURPLE = 12'hF0F;
localparam [11:0] RED = 12'hF00;
localparam [11:0] GREEN = 12'h00F;
localparam [11:0] BLUE = 12'h00F;
localparam [11:0] ORANGE = 12'hFA5;
localparam [11:0] BLACK = 12'h000;

wire [11:0] tile_color;

tilemap u_tiles (
    .h_count(h_count),
    .v_count(v_count),
    .color(tile_color)
);


wire is_checker = h_count[5] ^ v_count[5];

wire in_box = (h_count >= offset_x) && (h_count < offset_x + BOX_SIZE) &&
                (v_count >= offset_y) && (v_count < offset_y + BOX_SIZE);

always @(*) begin
    {r, g, b} = BLACK;
    if (active_video) begin
        {r, g, b} = tile_color;

        if (in_box)
            {r, g, b} = ORANGE;
    end
end
endmodule
