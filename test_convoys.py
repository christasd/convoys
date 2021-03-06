import datetime
import matplotlib
import numpy
import pytest
import random
import scipy.stats
matplotlib.use('Agg')  # Needed for matplotlib to run in Travis
import convoys
import convoys.regression


def sample_weibull(k, lambd):
    # scipy.stats is garbage for this
    # exp(-(x * lambda)^k) = y
    return (-numpy.log(random.random())) ** (1.0/k) / lambd


def test_exponential_regression_model(c=0.3, lambd=0.1, n=100000):
    # With a really long observation window, the rate should converge to the measured
    X = numpy.ones((n, 1))
    B = numpy.array([bool(random.random() < c) for x in range(n)])
    T = numpy.array([scipy.stats.expon.rvs(scale=1.0/lambd) if b else 1000.0 for b in B])
    c = numpy.mean(B)
    model = convoys.regression.ExponentialRegression()
    model.fit(X, B, T)
    assert 0.95*c < model.predict_final([1]) < 1.05*c
    t = 10
    d = 1 - numpy.exp(-lambd*t)
    assert 0.95*c*d < model.predict([1], t) < 1.05*c*d

    # Check the confidence intervals
    y, y_lo, y_hi = model.predict_final([1], ci=0.95)
    c_lo = scipy.stats.beta.ppf(0.025, n*c, n*(1-c))
    c_hi = scipy.stats.beta.ppf(0.975, n*c, n*(1-c))
    assert 0.95*c < y < 1.05 * c
    assert 0.95*c_lo < y_lo < 1.05 * c_lo
    assert 0.95*c_hi < y_hi < 1.05 * c_hi


def test_weibull_regression_model(cs=[0.3, 0.5, 0.7], lambd=0.1, k=0.5, n=100000):
    X = numpy.array([[1] + [r % len(cs) == j for j in range(len(cs))] for r in range(n)])
    B = numpy.array([bool(random.random() < cs[r % len(cs)]) for r in range(n)])
    T = numpy.array([b and sample_weibull(k, lambd) or 1000 for b in B])
    model = convoys.regression.WeibullRegression()
    model.fit(X, B, T)
    for r, c in enumerate(cs):
        x = [1] + [int(r == j) for j in range(len(cs))]
        assert 0.95 * c < model.predict_final(x) < 1.05 * c


def test_weibull_regression_model_ci(c=0.3, lambd=0.1, k=0.5, n=100000):
    X = numpy.ones((n, 1))
    B = numpy.array([bool(random.random() < c) for r in range(n)])
    c = numpy.mean(B)
    T = numpy.array([b and sample_weibull(k, lambd) or 1000 for b in B])

    model = convoys.regression.WeibullRegression()
    model.fit(X, B, T)
    y, y_lo, y_hi = model.predict_final([1], ci=0.95)
    c_lo = scipy.stats.beta.ppf(0.025, n*c, n*(1-c))
    c_hi = scipy.stats.beta.ppf(0.975, n*c, n*(1-c))
    assert 0.95*c < y < 1.05 * c
    assert 0.95*(c_hi-c_lo) < (y_hi-y_lo) < 1.05 * (c_hi-c_lo)


def test_gamma_regression_model(c=0.3, lambd=0.1, k=3.0, n=100000):
    X = numpy.ones((n, 1))
    B = numpy.array([bool(random.random() < c) for r in range(n)])
    T = numpy.array([b and scipy.stats.gamma.rvs(a=k, scale=1.0/lambd) or 1000 for b in B])
    model = convoys.regression.GammaRegression()
    model.fit(X, B, T)
    assert 0.95*c < model.predict_final([1]) < 1.05*c
    assert 0.95*k < model.params['k'] < 1.05*k


def _get_data(c=0.3, k=10, lambd=0.1, n=1000):
    data = []
    now = datetime.datetime(2000, 7, 1)
    for x in range(n):
        date_a = datetime.datetime(2000, 1, 1) + datetime.timedelta(days=random.random()*100)
        if random.random() < c:
            delay = scipy.stats.gamma.rvs(a=k, scale=1.0/lambd)
            date_b = date_a + datetime.timedelta(days=delay)
            if date_b < now:
                data.append(('foo', date_a, date_b, now))
            else:
                data.append(('foo', date_a, None, now))
        else:
            data.append(('foo', date_a, None, now))
    return data


def test_plot_cohorts():
    convoys.plot_cohorts(_get_data(), projection='gamma')


@pytest.mark.skip
def test_plot_conversion():
    convoys.plot_timeseries(_get_data(), window=datetime.timedelta(days=7), model='gamma')
