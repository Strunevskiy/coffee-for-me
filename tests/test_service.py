import pytest
from mock import Mock

from src.base.entity import POSITION, TYPE, Order, Item, User, ReportRecord
from src.service.exception import ServiceError
from src.service.exporter import ConsoleExporter
from src.service.service import ReportService, OrderService
from src.store.dao import DaoManager
from src.store.db import DataSource


@pytest.mark.service
class TestOrderService(object):

    @pytest.fixture
    def mock_dao_manager(self):
        return Mock(spec=DaoManager(DataSource()))

    @pytest.fixture
    def mock_console_exporter(self):
        return Mock(spec=ConsoleExporter())

    @pytest.fixture
    def order_service(self, mock_dao_manager):
        return OrderService(mock_dao_manager)

    @pytest.fixture
    def report_service(self, mock_dao_manager):
        return ReportService(mock_dao_manager)

    @pytest.fixture
    def valid_order(self):
        test_order = Order(User("Oleg", "Strunevskiy", POSITION.MANAGER))
        test_order.add_items(Item("late", 2.0000, TYPE.ADDITION), Item("espresso", 2.0000, TYPE.BEVERAGE))
        return test_order

    @pytest.fixture
    def invalid_order(self):
        return Order(User("Oleg", "Strunevskiy", POSITION.MANAGER))

    def test_order_service_save_valid_order(self, mock_dao_manager, order_service, valid_order):
        order_id = 1
        mock_dao_manager.get_order_dao().insert.return_value = order_id

        order_service.save(valid_order)

        mock_dao_manager.get_order_dao().insert.assert_called_with(valid_order)
        for item in valid_order.get_items():
            mock_dao_manager.get_item_dao().insert.assert_any_call(item, order_id)

        mock_dao_manager.commit.assert_called_once()
        mock_dao_manager.close_connection.assert_called_once()

    def test_order_service_save_invalid_order(self, order_service, invalid_order):
        with pytest.raises(ServiceError, message='Expect ServiceError if order passed to service is without items'):
            order_service.save(invalid_order)

    def test_report_service_report_to_console(self, mock_dao_manager, report_service, mock_console_exporter):
        test_report_records = [ReportRecord("Test_0, Test1", 20, 20.1010),
                               ReportRecord("Test_2, Test_3", 10, 10.0101)]
        exp_export_data = [
            (report_record.get_fullname(), str(report_record.get_sales_number()), str(report_record.get_sales_value()))
            for report_record in test_report_records]
        exp_total_sales = str(sum([report_record.get_sales_number() for report_record in test_report_records]))
        exp_total_values = str(sum([report_record.get_sales_value() for report_record in test_report_records]))

        mock_dao_manager.get_report_dao().get_sales_records.return_value = test_report_records
        report_service.report(mock_console_exporter)
        mock_console_exporter.export.assert_called_once_with(exp_export_data, exp_total_sales, exp_total_values)

    def test_report_service_report_to_console_dao_return_nothing(self, mock_dao_manager, report_service, mock_console_exporter):
        mock_dao_manager.get_report_dao().get_sales_records.return_value = []
        with pytest.raises(ServiceError, message='Expect ServiceError if dao returns nothing'):
            report_service.report(mock_console_exporter)
