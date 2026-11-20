module breakout_brick_occupancy_tb;
    logic clk;
    logic rst;
    logic [27:0] bricks_hit;

    logic [27:0] brick_occupancy;
    breakout_brick_occupancy dut (
        .clk(clk),
        .rst(rst),
        .bricks_hit(bricks_hit),
        .brick_occupancy(brick_occupancy)
    );

    logic [27:0] expected;

    always #5 clk = ~clk;

    initial begin
        #500;
        $display("Simulation complete");
        $finish;
    end

    initial begin
        expected = '1;
        bricks_hit = '0;
        rst = 1;
        @(posedge clk) begin
            #2;
            assert (brick_occupancy === expected)
            else $error("Starting brick occupancy is not all 1, actual: %b", brick_occupancy);
        end

        #1 rst = 0;

        #1;

        bricks_hit[27] = 1;
        expected[27]   = 0;

        @(posedge clk) begin
            #1
            assert (brick_occupancy === expected)
            else $error("Expected bit 27 to be 0 | Actual: %b", brick_occupancy[27]);
            bricks_hit[27] = 0;
        end

        @(posedge clk) begin
            #1;

            assert (brick_occupancy === expected)
            else $error("Expected bit 27 to be 1 | Actual: %b", brick_occupancy[27]);
        end

    end


endmodule
;
