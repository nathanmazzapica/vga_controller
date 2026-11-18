module breakout_brick_occupancy(
    input logic clk,
    input logic rst,
    input logic [4:0] brick_addr,
    output logic [27:0] brick_occupancy
);

initial begin
    brick_occupancy = '1;
end

always_ff @(posedge clk) begin
    if (rst)
        brick_occupancy = '1;
end

endmodule
