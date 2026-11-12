`timescale 1ns / 1ps
module vram(
input wire clk,
input wire write_en,
input reg [7:0] data_in,
input wire [12:0] write_addr,
input wire [12:0] read_addr,
output reg [7:0] data_out
);

reg [7:0] vmem [0:4799];

initial begin 
    $readmemh("vram.mem", vmem);
end

always @(posedge clk) begin
    if (write_en)
        vmem[write_addr] <= data_in;
    data_out <= vmem[read_addr];
end

endmodule
