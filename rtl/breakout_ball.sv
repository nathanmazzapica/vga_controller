module breakout_ball (
    input logic clk,
    input logic rst,
    input logic move_tick,
    input logic reflect_x,
    input logic reflect_y,
    input logic serve,
    input logic [9:0] paddle_x,
    output logic [9:0] ball_x,
    output logic [9:0] ball_y,
    output logic [3:0] ball_vx,
    output logic [3:0] ball_vy
);

    // 4-bit signed
    logic [3:0] vel_x = 0;
    logic [3:0] vel_y = 0;

    logic waiting = 1;

    // Sign-magnitude velocity (bit 3 = negative), exposed for the bouncer
    assign ball_vx = vel_x;
    assign ball_vy = vel_y;

    initial begin
        ball_x <= 10'd320;
        ball_y <= 10'd430;
    end


    always_ff @(posedge clk) begin
        if (rst) begin
            ball_x  <= paddle_x + 50;
            ball_y  <= 10'd420;
            vel_x   <= 0;
            vel_y   <= -0;
            waiting <= 1;
        end else begin
            if (waiting) ball_x <= paddle_x + 50;
            if (serve & waiting) begin
                vel_x   <= 4'b0101;
                vel_y   <= 4'b1101;
                waiting <= 0;
            end

            if (reflect_x & move_tick) vel_x[3] = ~vel_x[3];
            if (reflect_y & move_tick) vel_y[3] = ~vel_y[3];


            if (move_tick & ~waiting) begin
                ball_x <= vel_x[3] ? ball_x - vel_x[2:0] : ball_x + vel_x[2:0];

                ball_y <= vel_y[3] ? ball_y - vel_y[2:0] : ball_y + vel_y[2:0];
            end
        end
    end
endmodule
