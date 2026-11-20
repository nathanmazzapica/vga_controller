module breakout_paddle #(
    parameter int PADDLE_W = 110
) (
    input logic clk,
    input logic rst,
    input logic move_tick,
    input logic [1:0] mov,
    output logic [9:0] paddle_x,
    output logic [9:0] paddle_y
);
    localparam RIGHT = 1, LEFT = 0;

    // Playfield interior is x = 170..489 (walls are tiles 16 and 49, 10 px each),
    // so the paddle's left edge stays >= 170 and its right edge <= 489.
    localparam int X_MIN = 170;
    localparam int X_MAX = 490 - PADDLE_W;

    always_ff @(posedge clk) begin
        if (rst) begin
            paddle_x <= 10'd270;
        end else begin
            if (move_tick) begin
                if (mov[RIGHT] && paddle_x < X_MAX) paddle_x <= paddle_x + 5;
                if (mov[LEFT] && paddle_x > X_MIN) paddle_x <= paddle_x - 5;
            end
        end
    end

    assign paddle_y = 10'd430;
endmodule
