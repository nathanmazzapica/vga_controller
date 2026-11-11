module vga_color(
    input wire [9:0] h_count,
    input wire [9:0] v_count,
    input wire active_video,
    input wire [9:0] offset_x, offset_y,
    output reg [3:0] r,g,b
);

integer sq_width = 32;
integer sq_height = 32;

wire checker = h_count[5] ^ v_count[5];

always @(*) begin
    r = 4'b0000;
    g = 4'b0000;
    b = 4'b0000;
    if (active_video) begin
        if (checker) begin
            r = 4'b0111;
            g = 4'b0000;
            b = 4'b1100;
        end

        if (h_count >= offset_x && h_count < offset_x + sq_width &&
            v_count >= offset_y && v_count < offset_y + sq_height) begin 
            r = 4'b0000;
            g = 4'b1111;
            b = 4'b0000;
        end


    end
    else begin
        r = 4'b0000;
        g = 4'b0000;
        b = 4'b0000;
    end
end
endmodule
