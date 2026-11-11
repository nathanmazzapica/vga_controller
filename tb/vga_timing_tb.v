`timescale 1ns/1ps

module vga_timing_tb;
reg clk = 0;
reg rst = 0;

wire hsync;
wire vsync;
//
// actual visible columns
// all values measured in clock cycles
localparam H_VISIBLE = 640;
localparam H_FP = 16;
localparam H_SYNC = 96;
localparam H_BP = 48;

localparam H_TOTAL = H_VISIBLE + H_FP + H_SYNC + H_BP;

// for vertical, values measured in lines
localparam V_VISIBLE = 480;
localparam V_FP = 10;
localparam V_SYNC = 2;
localparam V_BP = 29;

localparam V_TOTAL = V_VISIBLE + V_FP + V_SYNC + V_BP;

vga_timing dut(
    .clk(clk),
    .rst(rst),
    .hsync(hsync),
    .vsync(vsync)
);

// 1 / 25 MHz = 40ns cycle
always #20 clk = ~clk;

integer cycle = 0;
integer expected_h;
integer expected_v;

initial begin
    $dumpfile("vga.vcd");
    $dumpvars(0, vga_timing_tb);
    rst = 1;
    @(posedge clk);
    #1;
    rst = 0;

    repeat (420_000) begin
        @(posedge clk);
        #1;
        cycle = cycle + 1;
        expected_h = cycle % 800;
        expected_v = (cycle / 800) % 525;

        if (expected_h >= H_VISIBLE + H_FP &&
            expected_h < H_VISIBLE + H_FP + H_SYNC
        ) begin
            if (hsync !== 1'b0) begin
                $display("TEST FAILED: H_SYNC SHOULD BE LOW");
                $display ("Cycle : %0d", cycle);
                $display ("Expected H : %0d", expected_h);
            end
        end
        else begin
            if (hsync !== 1'b1) begin
                $display ("TEST FAILED: H_SYNC SHOULD BE LOW");
                $display ("Cycle : %0d", cycle);
                $display ("Expected H : %0d", expected_h);
            end
        end

        if (expected_v >= V_VISIBLE + V_FP &&
            expected_v < V_VISIBLE + V_FP + V_SYNC
        ) begin
            if (vsync !== 1'b0) begin
                $display("TEST FAILED: V_SYNC SHOULD BE LOW");
                $display ("Cycle : %0d", cycle);
                $display ("Expected V : %0d", expected_v);
            end
        end
        else begin
            if (vsync !== 1'b1) begin
                $display ("TEST FAILED: V_SYNC SHOULD BE LOW");
                $display ("Cycle : %0d", cycle);
                $display ("Expected V : %0d", expected_v);
            end
        end
    end
    $finish;
end

endmodule
