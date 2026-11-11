module box_mover(
    input wire clk,
    input wire rst,
    input wire frame_start,
    output reg [9:0] offset_x, offset_y
);

always @(posedge clk) begin
    if (rst) begin
        offset_x = 9'b0;
        offset_y = 9'b0;
    end
    else if (frame_start) begin
        offset_x = offset_x + 100;
        offset_y = offset_y + 100;
    end
end


endmodule
