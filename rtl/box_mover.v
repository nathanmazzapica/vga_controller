module box_mover(
    input wire clk,
    input wire rst,
    input wire frame_start,
    input wire [3:0] mov,
    output reg [9:0] offset_x, offset_y
);

localparam UP = 3, RIGHT = 2, LEFT = 1, DOWN = 0;

reg [2:0] frame_counter = 0;

wire move_tick = frame_start && (frame_counter == 3);

always @(posedge clk) begin
    if (rst) begin
        offset_x <= 10'b0;
        offset_y <= 10'b0;
        frame_counter <= 0;
    end
    if (move_tick) begin
        frame_counter <= 0;
        if (mov[UP])
            offset_y <= offset_y - 1;
        if (mov[DOWN])
            offset_y <= offset_y + 1;
        if (mov[RIGHT])
            offset_x <= offset_x + 1;
        if (mov[LEFT])
            offset_x <= offset_x - 1;
    end else begin
        frame_counter <= frame_counter + 1;
    end
end


endmodule
