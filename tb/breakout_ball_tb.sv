`timescale 1ns/1ps
module breakout_ball_tb;

logic clk, rst, move_tick, reflect_x, reflect_y, serve;
logic [9:0] ball_x, ball_y;

logic [9:0] cur_x, cur_y;

breakout_ball dut (
    .clk(clk),
    .rst(rst),
    .move_tick(move_tick),
    .reflect_x(reflect_x),
    .reflect_y(reflect_y),
    .serve(serve),
    .ball_x(ball_x),
    .ball_y(ball_y)
);

always #5 clk = ~clk;

initial begin
    $dumpfile("ball.vcd");
    $dumpvars(0, breakout_ball_tb);
    clk = 0;
    rst = 1;
    @(posedge clk) begin
        #1; // I learned this is needed because otherwise this posedge is shared with the
        // always_ff in the dut so NBAs wouldn't be reflected at the time of assertion
        // another solution is assert final but that isnt supported by icarus
        assert (dut.waiting === 1'b1)
        else $error("Expected waiting %b ; Actual %b", 1'b1, dut.waiting);
        assert (dut.vel_x === 4'b0)
        else $error("Expected velocity x to be 0 | Actual : %d", dut.vel_x);
        assert (dut.vel_y === 4'b0)
        else $error("Expected velocity y to be 0 | Actual : %d", dut.vel_y);
        assert (ball_x === 10'd320 && ball_y === 10'd430)
        else $error("Expected position to be (320, 430) | Actual : (%d, %d)", ball_x, ball_y);
    end
    cur_x = ball_x;
    cur_y = ball_y;
    rst = 0;
    serve = 1;


    @(posedge clk) begin
        #1;
        assert (dut.waiting === 1'b0)
        else $error("Expected waiting %b ; Actual %b", 1'b0, dut.waiting);
        assert (dut.vel_x[2:0] === 4'd5)
        else $error("Expected velocity x magnitude to be 5 | Actual : %d", dut.vel_x[2:0]);
        assert (dut.vel_y[2:0] === 4'd5)
        else $error("Expected velocity y magnitude to be 5 | Actual : %d", dut.vel_y[2:0]);

        assert (dut.vel_x[3] === 4'b0)
        else $error("Expected velocity x sign to be 0 | Actual : %b", dut.vel_x[3]);
        assert (dut.vel_y[3] === 4'b1)
        else $error("Expected velocity y sign to be 1 | Actual : %b", dut.vel_y[3]);
    end

    move_tick = 1;
    @(posedge clk) begin
        #1;
        assert (ball_x > cur_x)
        else $error("Expected ball position to increase from %d | Actual : %d", cur_x, ball_x);
        assert (ball_y < cur_y)
        else $error("Expected ball position to decrease from %d | Actual : %d", cur_y, ball_y);
        cur_x = ball_x;
        cur_y = ball_y;
    end
    move_tick = 0;
    @(posedge clk) begin
        #1;
        assert (ball_x === cur_x)
        else $error("Expected ball position x to be %d | Actual : %d", cur_x, ball_x);
        assert (ball_y === cur_y)
        else $error("Expected ball position y to be %d | Actual : %d", cur_y, ball_y);
        cur_x = ball_x;
        cur_y = ball_y;
    end

    reflect_x = 1;
    reflect_y = 1;

    @(posedge clk) begin
        #1;
        reflect_x = 0;
        reflect_y = 0;
        assert (dut.vel_x[2:0] === 4'd5)
        else $error("Expected velocity x magnitude to be 5 | Actual : %d", dut.vel_x[2:0]);
        assert (dut.vel_y[2:0] === 4'd5)
        else $error("Expected velocity y magnitude to be 5 | Actual : %d", dut.vel_y[2:0]);

        assert (dut.vel_x[3] === 4'b1)
        else $error("Expected velocity x sign to be 1 | Actual : %b", dut.vel_x[3]);
        assert (dut.vel_y[3] === 4'b0)
        else $error("Expected velocity y sign to be 0 | Actual : %b", dut.vel_y[3]);
    end

    reflect_x = 1;
    @(posedge clk) begin
        #1;
        assert (dut.vel_x[2:0] === 4'd5)
        else $error("Expected velocity x magnitude to be 5 | Actual : %d", dut.vel_x[2:0]);
        assert (dut.vel_y[2:0] === 4'd5)
        else $error("Expected velocity y magnitude to be 5 | Actual : %d", dut.vel_y[2:0]);

        assert (dut.vel_x[3] === 4'b0)
        else $error("Expected velocity x sign to be 0 | Actual : %b", dut.vel_x[3]);
        assert (dut.vel_y[3] === 4'b0)
        else $error("Expected velocity y sign to be 0 | Actual : %b", dut.vel_y[3]);
        reflect_x = 0;
    end

    reflect_y = 1;
    @(posedge clk) begin
        #1;
        assert (dut.vel_x[2:0] === 4'd5)
        else $error("Expected velocity x magnitude to be 5 | Actual : %d", dut.vel_x[2:0]);
        assert (dut.vel_y[2:0] === 4'd5)
        else $error("Expected velocity y magnitude to be 5 | Actual : %d", dut.vel_y[2:0]);

        assert (dut.vel_x[3] === 4'b0)
        else $error("Expected velocity x sign to be 0 | Actual : %b", dut.vel_x[3]);
        assert (dut.vel_y[3] === 4'b1)
        else $error("Expected velocity y sign to be 1 | Actual : %b", dut.vel_y[3]);
        reflect_y = 0;
    end

    rst = 1;
    @(posedge clk) begin
        #1; // I learned this is needed because otherwise this posedge is shared with the
        // always_ff in the dut so NBAs wouldn't be reflected at the time of assertion
        // another solution is assert final but that isnt supported by icarus
        assert (dut.waiting === 1'b1)
        else $error("Expected waiting %b ; Actual %b", 1'b1, dut.waiting);
        assert (dut.vel_x === 4'b0)
        else $error("Expected velocity x to be 0 | Actual : %d", dut.vel_x);
        assert (dut.vel_y === 4'b0)
        else $error("Expected velocity y to be 0 | Actual : %d", dut.vel_y);
        assert (ball_x === 10'd320 && ball_y === 10'd430)
        else $error("Expected position to be (320, 430) | Actual : (%d, %d)", ball_x, ball_y);
    end




    #500 $finish;
end


endmodule;
