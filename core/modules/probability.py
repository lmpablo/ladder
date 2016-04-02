def pairwise_probability_calculation(p_a, p_b):
    pr_a = 1 / float((10 ** -(p_a.rating - p_b.rating) / float(400)) + 1)

    win_p_a = pr_a
    lose_p_b = pr_a
    win_p_b = 1 - pr_a
    lose_p_a = 1 - pr_a

    return {
        p_a.player_id: {
            'win': win_p_a,
            'lose': lose_p_a
        },
        p_b.player_id: {
            'win': win_p_b,
            'lose': lose_p_b
        }
    }
