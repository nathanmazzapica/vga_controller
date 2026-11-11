`timescale 1ns/1ps
module vga_controller_tb;
reg clk = 0;
reg rst = 1;

integer file;

wire hsync;
wire vsync;
wire active_video;
reg [9:0] offset_x = 0;
reg [9:0] offset_y = 0;

wire [3:0] r,g,b;

vga_controller dut(
    .clk(clk),
    .rst(rst),
    .offset_x(offset_x),
    .offset_y(offset_y),
    .hsync(hsync),
    .vsync(vsync),
    .r(r),
    .g(g),
    .b(b),
    .active_video(active_video)
);

always #20 clk = ~clk;

integer pixels_written = 0;
integer direction_x = 1;
integer direction_y = 1;
integer frame;

initial begin
    @(posedge clk);
    #1;
    rst = 0;
    //$dumpfile("vga_controller.vcd");
    //$dumpvars(0, vga_controller_tb);
    for (frame = 0; frame < 120; frame = frame + 1) begin
        file = $fopen($sformatf("frame_%03d.ppm", frame), "w");
        if (file == 0)
            $fatal(1, "Failed to open output.ppm");
        $fwrite(file, "P3\n640 480\n15\n");
        repeat (800 * 521) begin
            if (active_video) begin
                $fwrite(file, "%0d %0d %0d\n", r, g, b);
                pixels_written = pixels_written + 1;
            end
            @(posedge clk);
            #1;
        end
        if (pixels_written != 640 * 480 * (frame+1))
            $display("FAIL: Expected 307200 pixels, got %0d", pixels_written);
        else
            $display("PASS: Captured %0d pixels", pixels_written);
        $fclose(file);

        if (direction_x == 1) begin
            if (offset_x >= 640 - 32 - 64) begin
                offset_x = 640 - 32;
                direction_x = -1;
            end
            else
                offset_x = offset_x + 64;
        end
        else begin
            if (offset_x <= 64) begin
                offset_x = 0;
                direction_x = 1;
            end
            else
                offset_x = offset_x - 64;
        end

        if (direction_y == 1) begin
            if (offset_y >= 480 - 32 - 64) begin
                offset_y = 480 - 32;
                direction_y = -1;
            end
            else
                offset_y = offset_y + 64;
        end
        else begin
            if (offset_y <= 64) begin
                offset_y = 0;
                direction_y = 1;
            end
            else
                offset_y = offset_y - 64;
        end
        /*
        offset_x = offset_x + (32 * direction_x);
        offset_y = offset_y + (32 * direction_y);

        if (offset_x + 32 >= 640) begin
            offset_x = 640-32;
            direction_x = -1;
        end
        else if (offset_x <= 0)
            direction_x = 1;

        if (offset_y + 32 >= 480)
            direction_y = -1;
        else if (offset_y <= 0)
            direction_y = 1;

        */
   end
   $finish;
end
endmodule

