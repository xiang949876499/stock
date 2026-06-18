from src.trading.scheduler import TradingScheduler


class DummyEngine:
    def is_running(self):
        return True


def _job_by_id(scheduler: TradingScheduler, job_id: str):
    return scheduler.scheduler.get_job(job_id)


def _cron_field(job, field_name: str) -> str:
    return str(next(field for field in job.trigger.fields if field.name == field_name))


def test_trading_scheduler_monitors_kline_during_a_share_sessions_and_reviews_after_close():
    scheduler = TradingScheduler()

    scheduler.setup(DummyEngine())

    morning_monitor = _job_by_id(scheduler, "short_term_kline_monitor_morning")
    afternoon_monitor = _job_by_id(scheduler, "short_term_kline_monitor_afternoon")
    post_market = _job_by_id(scheduler, "post_market_trading_review")

    assert morning_monitor is not None
    assert _cron_field(morning_monitor, "day_of_week") == "mon-fri"
    assert _cron_field(morning_monitor, "hour") == "9-11"
    assert _cron_field(morning_monitor, "minute") == "*/5"

    assert afternoon_monitor is not None
    assert _cron_field(afternoon_monitor, "day_of_week") == "mon-fri"
    assert _cron_field(afternoon_monitor, "hour") == "13-14"
    assert _cron_field(afternoon_monitor, "minute") == "*/5"

    assert post_market is not None
    assert _cron_field(post_market, "day_of_week") == "mon-fri"
    assert _cron_field(post_market, "hour") == "15"
    assert _cron_field(post_market, "minute") == "35"


def test_trading_scheduler_jobs_do_not_overlap(monkeypatch):
    scheduler = TradingScheduler()
    added_jobs = {}

    original_add_job = scheduler.scheduler.add_job

    def capture_add_job(*args, **kwargs):
        added_jobs[kwargs["id"]] = kwargs
        return original_add_job(*args, **kwargs)

    monkeypatch.setattr(scheduler.scheduler, "add_job", capture_add_job)

    scheduler.setup(DummyEngine())

    assert added_jobs["short_term_kline_monitor_morning"]["max_instances"] == 1
    assert added_jobs["short_term_kline_monitor_morning"]["coalesce"] is True
    assert added_jobs["short_term_kline_monitor_afternoon"]["max_instances"] == 1
    assert added_jobs["short_term_kline_monitor_afternoon"]["coalesce"] is True
    assert added_jobs["post_market_trading_review"]["max_instances"] == 1
    assert added_jobs["post_market_trading_review"]["coalesce"] is True


def test_start_schedules_immediate_analysis(monkeypatch):
    scheduler = TradingScheduler()
    scheduler.setup(DummyEngine())
    scheduled_jobs = []

    monkeypatch.setattr(scheduler.scheduler, "start", lambda: None)

    original_add_job = scheduler.scheduler.add_job

    def capture_add_job(*args, **kwargs):
        scheduled_jobs.append(kwargs)
        return original_add_job(*args, **kwargs)

    monkeypatch.setattr(scheduler.scheduler, "add_job", capture_add_job)

    scheduler.start()

    assert "startup_trading_analysis" in {kwargs["id"] for kwargs in scheduled_jobs}
    startup_kwargs = next(
        kwargs for kwargs in scheduled_jobs if kwargs["id"] == "startup_trading_analysis"
    )
    assert startup_kwargs["max_instances"] == 1
    assert startup_kwargs["coalesce"] is True


def test_stop_does_not_wait_for_running_analysis(monkeypatch):
    scheduler = TradingScheduler()
    shutdown_calls = []

    def capture_shutdown(*args, **kwargs):
        shutdown_calls.append(kwargs)

    monkeypatch.setattr(scheduler.scheduler, "shutdown", capture_shutdown)

    scheduler.stop()

    assert shutdown_calls == [{"wait": False}]
