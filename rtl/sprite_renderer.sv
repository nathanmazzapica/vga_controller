module sprite_renderer#(parameter int N=4) (
    input logic [9:0] h_count, v_count,
    input logic [N-1:0] [9:0] x,
    input logic [N-1:0] [9:0] y,
    output logic any_hit
);

logic [N-1:0] hit;

for (genvar i = 0; i < N; i++) begin : spr
    sprite u_sprite(
        .*, .x(x[i]), .y(y[i]), .hit(hit[i])
    );
end

always_comb any_hit = |hit;

endmodule;
