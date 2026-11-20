`timescale 1ns / 1ps
module breakout (
    input logic clk,
    input logic btnC,
    input logic btnU,
    btnR,
    btnL,
    btnD,
    output [3:0] vgaRed,
    output [3:0] vgaBlue,
    output [3:0] vgaGreen,
    output Hsync,
    Vsync
);

    wire pix_clk, locked;

    wire [1:0] mov = {btnR, btnL};


    clk_wiz_0 u_clk (
        .clk_in1(clk),
        .reset(btnC),
        .clk_out1(pix_clk),
        .locked(locked)
    );

    logic active_video;
    logic frame_start;

    wire rst = btnC | ~locked;

    logic [9:0] h_count;
    logic [9:0] v_count;

    vga_timing u_vga_timing (
        .clk(pix_clk),
        .rst(rst),
        .hsync(Hsync),
        .vsync(Vsync),
        .active_video(active_video),
        .frame_start(frame_start),
        .h_count(h_count),
        .v_count(v_count)
    );

    logic move_tick;
    move_ticker u_move_ticker (
        .clk(pix_clk),
        .rst(rst),
        .frame_start(frame_start),
        .move_tick(move_tick)
    );

    localparam int PADDLE_W = 70;  // paddle width in px (draw + travel + collision)

    logic [9:0] paddle_x;
    logic [9:0] paddle_y;

    breakout_paddle #(
        .PADDLE_W(PADDLE_W)
    ) u_paddle (
        .clk(pix_clk),
        .rst(rst),
        .move_tick(move_tick),
        .mov(mov),
        .paddle_x(paddle_x),
        .paddle_y(paddle_y)
    );

    logic [9:0] ball_x;
    logic [9:0] ball_y;
    logic [3:0] ball_vx;
    logic [3:0] ball_vy;
    logic bounce_x;
    logic bounce_y;

    breakout_ball u_ball (
        .clk(pix_clk),
        .rst(rst),
        .move_tick(move_tick),
        .reflect_x(bounce_x),
        .reflect_y(bounce_y),
        .serve(btnU),
        .paddle_x(paddle_x),
        .ball_x(ball_x),
        .ball_y(ball_y),
        .ball_vx(ball_vx),
        .ball_vy(ball_vy)
    );

    logic [27:0] brick_occupancy;
    logic [27:0] bricks_hit;
    breakout_brick_occupancy u_brick_occupancy (
        .clk(pix_clk),
        .rst(rst),
        .move_tick(move_tick),
        .bricks_hit(bricks_hit),
        .brick_occupancy(brick_occupancy)
    );

    breakout_ball_bouncer #(
        .PADDLE_W(PADDLE_W)
    ) u_bouncer (
        .ball_x(ball_x),
        .ball_y(ball_y),
        .ball_vx(ball_vx),
        .ball_vy(ball_vy),
        .paddle_x(paddle_x),
        .paddle_y(paddle_y),
        .brick_occupancy(brick_occupancy),
        .bricks_hit(bricks_hit),
        .bounce_x(bounce_x),
        .bounce_y(bounce_y)
    );




    logic draw_wall;
    logic draw_bg;
    logic draw_brick;
    breakout_tilemap u_tilemap (
        .h_count(h_count),
        .v_count(v_count),
        .brick_occupancy(brick_occupancy),
        .draw_wall(draw_wall),
        .draw_bg(draw_bg),
        .draw_brick(draw_brick)
    );

    logic draw_player;
    assign draw_player  = (h_count >= paddle_x) & (h_count < paddle_x + PADDLE_W)
                    & (v_count >= paddle_y) & (v_count < paddle_y + 10);

    logic draw_ball;
    assign draw_ball    = (h_count >= ball_x) & (h_count < ball_x + 10)
                        & (v_count >= ball_y) & (v_count < ball_y + 10);

    breakout_color u_color (
        .active_video(active_video),
        .draw_wall(draw_wall),
        .draw_bg(draw_bg),
        .draw_brick(draw_brick),
        .draw_player(draw_player),
        .draw_ball(draw_ball),
        .r(vgaRed),
        .g(vgaGreen),
        .b(vgaBlue)
    );
endmodule
