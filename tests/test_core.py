"""Unit tests for the maths in main.py. Run: python tests/test_core.py"""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src"))
import numpy as np
import main as M

rng = np.random.default_rng(0)


def rand_q(n):
    q = rng.standard_normal((n, 4)); return q / np.linalg.norm(q, axis=1)[:, None]


def Rm(q):
    w, x, y, z = q
    return np.array([[1-2*(y*y+z*z), 2*(x*y-w*z), 2*(x*z+w*y)], [2*(x*y+w*z), 1-2*(x*x+z*z), 2*(y*z-w*x)],
                     [2*(x*z-w*y), 2*(y*z+w*x), 1-2*(x*x+y*y)]])


def test_hamilton_convention():
    i = np.array([[0., 1, 0, 0]]); j = np.array([[0., 0, 1, 0]]); k = np.array([[0., 0, 0, 1]])
    assert np.allclose(M.quat_mul(i, j), k) and np.allclose(M.quat_mul(j, i), -k)       # ij = k (Hamilton)


def test_rotate_matches_matrix_and_composes():
    a, b = rand_q(50), rand_q(50); v = rng.standard_normal((50, 3))
    assert np.allclose(M.quat_rotate(a, v), np.einsum("nij,nj->ni", np.array([Rm(q) for q in a]), v))
    assert np.allclose(M.quat_rotate(M.quat_mul(a, b), v), M.quat_rotate(a, M.quat_rotate(b, v)))  # R(ab) = R(a)R(b)


def test_exp_small_and_large_and_direction():
    q = M.quat_exp(np.array([[0, 0, np.pi / 2], [0, 0, 1e-12], [0, 0, 0]]))
    assert np.allclose(M.quat_rotate(q[:1], np.array([[1., 0, 0]])), [[0, 1, 0]])         # +90 deg about z: x -> y
    assert np.allclose(np.linalg.norm(q, axis=1), 1) and np.allclose(q[2], [1, 0, 0, 0])


def test_cumprod_equals_loop():
    dq = M.quat_exp(rng.standard_normal((1000, 3)) * 0.05); ref = np.empty_like(dq); acc = np.array([1., 0, 0, 0])
    for n in range(1000):
        acc = M.quat_mul(acc[None], dq[n:n+1])[0]; ref[n] = acc
    assert np.allclose(M.quat_cumprod(dq), ref, atol=1e-10)


def test_tilt_from_gravity():
    for f in (np.array([0, 0, 9.8]), np.array([9.0, 0.5, -3.0]), np.array([0, 0, -9.8]), np.array([0.1, -9.7, 0.3])):
        q = M.tilt_from_gravity(f)
        assert np.allclose(M.quat_rotate(q[None], f[None])[0], [0, 0, np.linalg.norm(f)], atol=1e-9)


def test_preintegration_constant_rate_and_gravity():
    # body spinning about z at 1 rad/s while at rest in gravity: world specific force stays (0,0,g)
    dt = 0.005; m = 10; t = (np.arange(m + 1) * dt)[None]
    g = np.tile([0, 0, 1.0], (1, m + 1, 1)); a = np.tile([0, 0, M.G], (1, m + 1, 1))
    dq, dv, dp, th = M.preintegrate_group(t, g, a)
    assert np.allclose(th, [[0, 0, m * dt]]) and np.allclose(dq[0], M.quat_exp(np.array([[0, 0, m * dt]]))[0])
    assert np.allclose(dv, [[0, 0, M.G * m * dt]]) and np.allclose(dp, [[0, 0, 0.5 * M.G * (m * dt) ** 2]])


def test_cumint_is_exact_for_constant_acceleration():
    dt = np.full(100, 0.05); vel, pos = M.cumint(np.full((100, 3), 2.0), dt)
    assert np.allclose(vel[-1], 10.0) and np.allclose(pos[-1], 0.5 * 2.0 * 25.0)


def test_timestamp_formatting_is_exact():
    ts = np.array([1403636579758555392, 1403636579763555584], dtype=np.int64)
    assert M.format_timestamps(ts, 1e-9) == ["1403636579.758555392", "1403636579.763555584"]


def test_poses_at_interpolation_and_tail():
    tn = np.array([0., 1, 2]); p = np.array([[0., 0, 0], [1, 0, 0], [2, 0, 0]]); v = np.tile([1., 0, 0], (3, 1))
    q = np.tile([1., 0, 0, 0], (3, 1)); cfg = dict(M.CFG)
    P, Q = M.poses_at(np.array([0.5, 0.5, 1.5, 7.0, -1.0]), tn, q, p, v, cfg)
    assert np.allclose(P[0], [0.5, 0, 0]) and np.allclose(P[0], P[1]) and np.allclose(P[2], [1.5, 0, 0])   # duplicates -> same pose
    assert 2.0 <= P[3, 0] <= 2.0 + cfg["blind_tau_s"] + 1e-9 and np.allclose(P[4], [0, 0, 0])                # damped tail; clamp before start
    assert np.allclose(np.linalg.norm(Q, axis=1), 1)


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for f in fns:
        f(); print("ok  ", f.__name__)
    print("%d tests passed" % len(fns))
