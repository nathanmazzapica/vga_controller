module sprite#(parameter int W = 32, H = 32) (
    input logic [9:0] h_count, v_count,
    input logic [9:0] x, y,
    output logic hit
    ); 

    always_comb
        hit = (h_count >= x) && (h_count < x + W) &&
            (v_count >= y) && (v_count < y + H);

endmodule
