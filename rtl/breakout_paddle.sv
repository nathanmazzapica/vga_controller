module breakout_paddle(
    input logic clk,
    input logic rst,
    input logic frame_start,
    input logic [1:0] mov,
    output logic [9:0] paddle_x,
    output logic [9:0] paddle_y
    );
localparam RIGHT = 1, LEFT = 0;

logic [3:0] frame_counter;
logic move_tick;
assign move_tick = frame_start && (frame_counter == 8);

initial begin
    frame_counter = 0;
end

always_ff @(posedge clk) begin
    if (rst) begin
        paddle_x <= 10'd270;
        frame_counter <= 0;
    end else begin
        if (frame_start) begin
            if (frame_counter == 7)
                frame_counter <= 0;
            else
                frame_counter = frame_counter + 1;
        end
        if (move_tick) begin
            frame_counter <= 0;
            if (mov[RIGHT] && paddle_x < 490)
                paddle_x <= paddle_x + 1;
            if (mov[LEFT] && paddle_x > 17)
                paddle_x <= paddle_x -1;
        end
    end
end

assign paddle_y = 10'd430;
endmodule
