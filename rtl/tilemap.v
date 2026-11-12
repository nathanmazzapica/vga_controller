`timescale 1ns / 1ps
module tilemap (
    input wire [9:0] h_count,
    input wire [9:0] v_count,
    output wire [11:0] color
);

reg [3:0] tiles [0:299];
reg [11:0] palette [0:15];

initial begin
    $readmemh("tiles.mem", tiles);
    $readmemh("palette.mem", palette);
end



wire [4:0] tile_x = h_count[9:5];
wire [3:0] tile_y = v_count[8:5];
wire [8:0] row = {5'b0, tile_y};
wire [8:0] index = (row << 4) + (row << 2) + tile_x; //y * 20 cheap

assign color = palette[tiles[index]];

endmodule
