`timescale 1ns/1ps

module breakout_tilemap_tb;

    logic [9:0] h_count;
    logic [9:0] v_count;
    logic [27:0] brick_occupancy;

    logic draw_wall;
    logic draw_bg;
    logic draw_brick;

    breakout_tilemap dut (.*);

    task automatic check_tile(
        input logic [9:0] px,
        input logic [9:0] py,
        input logic expected_wall,
        input logic expected_bg,
        input logic expected_brick
    );
        h_count = px;
        v_count = py;

        #1; // Let combinational logic settle

        if ({draw_wall, draw_bg, draw_brick} !==
            {expected_wall, expected_bg, expected_brick}) begin

            $fatal(1,
                "FAIL at (%0d,%0d): got %b%b%b, expected %b%b%b",
                px, py,
                draw_wall, draw_bg, draw_brick,
                expected_wall, expected_bg, expected_brick
            );
        end
    endtask

    initial begin
        brick_occupancy = '0;
        brick_occupancy[0] = 1'b1;

        // Pixel (180,70) -> tile (18,7)
        // First brick is occupied
        check_tile(180, 70, 0, 1, 1);

        // Tile (18,9) is below that brick
        check_tile(180, 90, 0, 1, 0);

        // Left wall at tile X=16
        check_tile(160, 70, 1, 0, 0);

        // Outside the playfield
        check_tile(0, 0, 0, 0, 0);

        $display("All tests passed!");
        $finish;
    end

endmodule

