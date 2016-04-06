import math


def __calculate_expected(a, b, norm=400.0):
    """
    :type a: models.player.Player
    :type b: models.player.Player
    :type norm: float
    """
    q_a = a.rating / norm
    q_b = b.rating / norm

    return q_a / (q_a + q_b)


def calculate(winner, loser, winner_score=1.0, loser_score=0.0, point_diff=None):
    """
    Calculates the changes in rating for both winner and loser.

    :type winner: models.player.Player
    :type loser: models.player.Player
    :type winner_score: float
    :type loser_score: float
    :type point_diff: int or None
    :rtype: (float, float)
    """
    winner_exp = __calculate_expected(winner, loser)
    loser_exp = 1 - winner_exp

    if point_diff is None:
        mvm = 1.0
    else:
        abs_pd = abs(point_diff)
        elo_diff = winner.rating - loser.rating
        mvm = math.log1p(abs_pd) * (2.2 / (elo_diff * 0.001 + 2.2))

    winner_update = (mvm * winner.k_factor) * (winner_score - winner_exp)
    loser_update = (mvm * loser.k_factor) * (loser_score - loser_exp)

    return winner_update, loser_update


def calculate_and_update(winner, loser, draw=False, point_diff=None):
    """
    Calculates the changes in rating for both winner and loser and also
    updates their models

    :type winner: models.player.Player
    :type loser: models.player.Player
    :type draw: bool
    :type point_diff: int
    """
    if draw:
        winner_score = 0.5
        loser_score = 0.5
        point_diff = None
    else:
        winner_score = 1.0
        loser_score = 1.0
    winner_update, loser_update = calculate(winner, loser,
                                            winner_score, loser_score,
                                            point_diff)

    winner.rating += winner_update
    loser.rating += loser_update

    winner.save()
    loser.save()
