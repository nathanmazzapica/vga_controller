`timescale 1ns/1ps

module vga_timing(
    input wire clk,
    input wire rst,
    output wire hsync,
    output wire vsync,
    output wire active_video,
    output reg [9:0] h_count,
    output reg [9:0] v_count
);

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

always @(posedge clk) begin
    if (rst) begin
        h_count <= 0;
        v_count <= 0;
    end
    else begin
        if (h_count == H_TOTAL - 1) begin
            h_count <= 0;
            if (v_count == V_TOTAL - 1)
                v_count <= 0;
            else
                v_count <= v_count + 1'b1;
        end
        else
            h_count <= h_count + 1'b1;

    end
end

assign hsync = !(
    h_count >= H_VISIBLE + H_FP &&
    h_count < H_VISIBLE + H_FP + H_SYNC
);

assign vsync = !(
    v_count >= V_VISIBLE + V_FP &&
    v_count < V_VISIBLE + V_FP + V_SYNC
);

assign active_video = (h_count < H_VISIBLE) && (v_count < V_VISIBLE);

endmodule
