module breakout_tilemap(
    input logic [9:0] h_count,
    input logic [9:0] v_count,
    input logic [27:0] brick_occupancy,
    output logic draw_wall,
    output logic draw_bg,
    output logic draw_brick
    );

    logic [5:0] tile_x; 
    logic [5:0] tile_y; 

    assign tile_x = h_count / 10; 
    assign tile_y = v_count / 10; 

    assign draw_wall        =  ((tile_x == 16) | (tile_x == 49)
	                       && (tile_y >= 4)   & (tile_y <= 46))
	                       || ((tile_y == 4)  | (tile_y ==46)
	                       && (tile_x >=16)   & (tile_x <= 49));

    assign draw_bg      = (tile_x > 16) & (tile_x < 49)
                        & (tile_y > 4)  & (tile_y < 46);

    logic [27:0] brick_hits;

    genvar r, c;

    generate
    for (r = 0; r < 7; r = r + 1) begin : rows
        for (c = 0; c < 4; c = c + 1) begin : cols
            assign brick_hits[r*4+c] =
                brick_occupancy[r*4+c] &&
                tile_x >= (18 + c*8) &&
                tile_x <  (24 + c*8) &&
                tile_y >= (7 + r*3) &&
                tile_y <  (9 + r*3);
        end
    end
    endgenerate

    assign draw_brick = |brick_hits;

 endmodule
