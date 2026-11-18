module move_ticker#(parameter int frames = 0)(
    input logic clk,
    input logic rst,
    input logic frame_start,
    output logic move_tick
);
assign move_tick = frame_start && (frame_counter == frames);

logic [3:0] frame_counter;

always_ff @(posedge clk) begin
    if (rst)
        frame_counter = 0;
    if (frame_start) begin
        if (frame_counter == frames)
            frame_counter <= 0;
        else
            frame_counter <= frame_counter + 1;
    end
end

endmodule
