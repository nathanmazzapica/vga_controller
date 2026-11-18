module breakout_color(
    input logic active_video,
    input logic draw_wall,
    input logic draw_bg,
    input logic draw_brick,
    input logic draw_player,
    output logic [3:0] r, g, b
);

localparam [11:0] RED = 12'hF00;
localparam [11:0] WALL = 12'h00F;
localparam [11:0] BACKGROUND = 12'h477;
localparam [11:0] BLACK = 12'h000;
localparam [11:0] WHITE = 12'hFFF;


logic [11:0] color;


always_comb begin
    color = BLACK;
    if (active_video) begin
        if (draw_wall)
            color = WALL;
        if (draw_bg)
            color = BACKGROUND;
        if (draw_brick)
            color = RED;
        if (draw_player)
            color = WHITE;
    end
end

assign {r, g, b} = color;

endmodule
