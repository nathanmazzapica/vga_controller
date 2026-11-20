module breakout_ball_bouncer #(
    parameter int PADDLE_W = 110,
    parameter int BALL_W   = 10
) (
    input logic [9:0] ball_x,
    input logic [9:0] ball_y,
    input logic [3:0] ball_vx,
    input logic [3:0] ball_vy,
    input logic [9:0] paddle_x,
    input logic [9:0] paddle_y,
    input logic [27:0] brick_occupancy,
    output logic [27:0] bricks_hit,
    output logic bounce_x,
    output logic bounce_y
);

    logic [9:0] ball_x_n;
    logic [9:0] ball_y_n;
    assign ball_x_n = ball_vx[3] == 0 ? ball_x + ball_vx[2:0] : ball_x - ball_vx[2:0];
    assign ball_y_n = ball_vy[3] == 0 ? ball_y + ball_vy[2:0] : ball_y - ball_vy[2:0];

    logic [27:0] brick_hits;
    logic hit_brick;
    genvar r, c;

    generate
        for (r = 0; r < 7; r = r + 1) begin : rows
            for (c = 0; c < 4; c = c + 1) begin : cols
                assign brick_hits[r*4+c] =
                brick_occupancy[r*4+c] &&
                ball_x_n >= (180 + c*80) &&
                ball_x_n <  (240 + c*80) &&
                ball_y_n >= (70 + r*30) &&
                ball_y_n <  (90 + r*30);
            end
        end
    endgenerate


    assign bricks_hit = brick_hits;
    assign hit_brick  = |brick_hits;



    logic over_paddle;
    logic hit_paddle;
    assign over_paddle = (ball_x_n + BALL_W > paddle_x) & (ball_x_n < paddle_x + PADDLE_W);
    assign hit_paddle  = ~ball_vy[3]
                       & (ball_y + BALL_W <= paddle_y)
                       & (ball_y_n + BALL_W >= paddle_y)
                       & over_paddle;

    assign bounce_x = ((ball_x_n <= 170) | (ball_x_n >= 480)) | hit_brick;
    assign bounce_y = (ball_y_n <= 40) | hit_paddle | hit_brick;

endmodule
