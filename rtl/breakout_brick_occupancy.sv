module breakout_brick_occupancy (
    input logic clk,
    input logic rst,
    input logic [27:0] bricks_hit,
    output logic [27:0] brick_occupancy
);

    initial begin
        brick_occupancy = '1;
    end

    always_ff @(posedge clk) begin
        if (rst) brick_occupancy = '1;
        else begin
            brick_occupancy <= brick_occupancy & ~bricks_hit;
        end
    end

endmodule
