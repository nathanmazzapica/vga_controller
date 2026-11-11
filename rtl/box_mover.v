module box_mover(
    input wire clk,
    input wire rst,
    input wire frame_start,
    input wire [3:0] mov,
    output reg [9:0] offset_x, offset_y
);

localparam UP = 3, RIGHT = 2, LEFT = 1, DOWN = 0;

always @(posedge clk) begin
    if (rst) begin
        offset_x <= 10'b0;
        offset_y <= 10'b0;
    end
    else if (frame_start) begin
        if (mov[UP])
            offset_y <= offset_y - 10;
        if (mov[DOWN])
            offset_y <= offset_y + 10;
        if (mov[RIGHT])
            offset_x <= offset_x + 10;
        if (mov[LEFT])
            offset_x <= offset_x - 10;
    end
end


endmodule
