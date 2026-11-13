`timescale 1ns / 1ps
module text_renderer (
    input wire [9:0] h_count,
    input wire [9:0] v_count,
    output wire [12:0] index
);


wire [6:0] tile_x = h_count[9:3];
wire [5:0] tile_y = v_count[8:3];

wire [12:0] row = {7'b0, tile_y};

assign index = (row << 6) + (row << 4) + tile_x;

endmodule
