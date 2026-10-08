from summer.inversion_of_control.dependencies import autowired, service

from src.health.application.check_health.i_check_health_use_case import ICheckHealthUseCase
from src.health.domain.bo.health_report import HealthReport
from src.health.domain.repositories.i_health_query_service import IHealthQueryService


@service()
class CheckHealthUseCase(ICheckHealthUseCase):
    @autowired
    def __init__(self, health_query_service: IHealthQueryService):
        self.health_query_service = health_query_service

    def execute(self) -> HealthReport:
        """Collects every dependency check and builds the report. Adding a future dependency
        (cache, queue, ...) means adding a check here, not touching the router."""
        return HealthReport(checks=[self.health_query_service.check_database_connection()])
