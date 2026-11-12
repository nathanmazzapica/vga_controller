`timescale 1ns / 1ps

module tilemap_tb;

    reg [9:0] h_count, v_count;
    wire [11:0] color;

    tilemap dut (
        .h_count(h_count),
        .v_count(v_count),
        .color(color)
    );

    task check_tile;
        input [9:0] x, y;
        reg [8:0] expected_index;
        reg [3:0] expected_tile;
        reg [11:0] expected_color;
        begin
            h_count = x;
            v_count = y;
            #10;

            expected_index = (y / 32) * 20 + (x / 32);
            expected_tile = dut.tiles[expected_index];
            expected_color = dut.palette[expected_tile];

            $display(
                "x=%0d y=%0d | index=%0d | tile=%h | color=%h | expected=%h",
                x, y, dut.index, expected_tile, color, expected_color
            );

            if (dut.index !== expected_index)
                $display("FAIL: Incorrect tile index!");

            if (color !== expected_color)
                $display("FAIL: Incorrect color!");

            if (^color === 1'bx)
                $display("WARNING: Color contains X/Z!");
        end
    endtask

    initial begin
        h_count = 0;
        v_count = 0;

        #10;

        $display("=== TILEMAP TEST ===");
        $display("tiles[0] = %h", dut.tiles[0]);
        $display("palette[0] = %h", dut.palette[0]);

        check_tile(0, 0);
        check_tile(31, 31);
        check_tile(32, 0);
        check_tile(0, 32);
        check_tile(320, 240);
        check_tile(639, 479);

        $display("=== TEST COMPLETE ===");
        $finish;
    end

endmodule
