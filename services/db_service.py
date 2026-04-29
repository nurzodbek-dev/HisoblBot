from datetime import datetime, timedelta, timezone

from sqlalchemy import select, func as sa_func
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from models import Base, Transaction, User
from models.transaction import TransactionType
from utils.config import config

engine = create_async_engine(config.DATABASE_URL, echo=False, pool_pre_ping=True)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def init_db() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_or_create_user(
    telegram_id: int,
    username: str | None = None,
    full_name: str | None = None,
) -> User:
    async with async_session() as session:
        result = await session.execute(
            select(User).where(User.telegram_id == telegram_id)
        )
        user = result.scalar_one_or_none()
        if user is None:
            user = User(
                telegram_id=telegram_id,
                username=username,
                full_name=full_name,
            )
            session.add(user)
            await session.commit()
            await session.refresh(user)
        return user


async def add_transaction(
    telegram_id: int,
    tx_type: TransactionType,
    amount: float,
    item: str | None = None,
    category: str | None = None,
    description: str | None = None,
    raw_input: str | None = None,
) -> Transaction:
    async with async_session() as session:
        result = await session.execute(
            select(User).where(User.telegram_id == telegram_id)
        )
        user = result.scalar_one_or_none()
        if user is None:
            user = User(telegram_id=telegram_id)
            session.add(user)
            await session.commit()
            await session.refresh(user)

        tx = Transaction(
            user_id=user.id,
            telegram_id=telegram_id,
            type=tx_type,
            amount=amount,
            item=item,
            category=category,
            description=description,
            raw_input=raw_input,
        )
        session.add(tx)
        await session.commit()
        await session.refresh(tx)
        return tx


async def get_transactions(
    telegram_id: int,
    tx_type: TransactionType | None = None,
    days: int | None = None,
    start_date: datetime | None = None,
    end_date: datetime | None = None,
) -> list[Transaction]:
    async with async_session() as session:
        stmt = select(Transaction).where(Transaction.telegram_id == telegram_id)
        if tx_type:
            stmt = stmt.where(Transaction.type == tx_type)
        if days:
            cutoff = datetime.now(timezone.utc) - timedelta(days=days)
            stmt = stmt.where(Transaction.created_at >= cutoff)
        if start_date:
            stmt = stmt.where(Transaction.created_at >= start_date)
        if end_date:
            stmt = stmt.where(Transaction.created_at <= end_date)
        stmt = stmt.order_by(Transaction.created_at.desc())
        result = await session.execute(stmt)
        return list(result.scalars().all())


async def get_summary(
    telegram_id: int,
    days: int | None = None,
    start_date: datetime | None = None,
    end_date: datetime | None = None,
) -> dict:
    async with async_session() as session:
        base_filter = [Transaction.telegram_id == telegram_id]
        if days:
            cutoff = datetime.now(timezone.utc) - timedelta(days=days)
            base_filter.append(Transaction.created_at >= cutoff)
        if start_date:
            base_filter.append(Transaction.created_at >= start_date)
        if end_date:
            base_filter.append(Transaction.created_at <= end_date)

        # Total income
        inc_result = await session.execute(
            select(sa_func.coalesce(sa_func.sum(Transaction.amount), 0)).where(
                *base_filter, Transaction.type == TransactionType.INCOME
            )
        )
        total_income = float(inc_result.scalar() or 0)

        # Total expense
        exp_result = await session.execute(
            select(sa_func.coalesce(sa_func.sum(Transaction.amount), 0)).where(
                *base_filter, Transaction.type == TransactionType.EXPENSE
            )
        )
        total_expense = float(exp_result.scalar() or 0)

        # Category breakdown for expenses
        cat_result = await session.execute(
            select(
                Transaction.category,
                sa_func.sum(Transaction.amount),
                sa_func.count(Transaction.id),
            )
            .where(*base_filter, Transaction.type == TransactionType.EXPENSE)
            .group_by(Transaction.category)
        )
        expense_by_category = [
            {"category": row[0] or "Boshqa", "total": float(row[1]), "count": row[2]}
            for row in cat_result.all()
        ]

        # Category breakdown for income
        inc_cat_result = await session.execute(
            select(
                Transaction.category,
                sa_func.sum(Transaction.amount),
                sa_func.count(Transaction.id),
            )
            .where(*base_filter, Transaction.type == TransactionType.INCOME)
            .group_by(Transaction.category)
        )
        income_by_category = [
            {"category": row[0] or "Boshqa", "total": float(row[1]), "count": row[2]}
            for row in inc_cat_result.all()
        ]

        # Transaction count
        count_result = await session.execute(
            select(sa_func.count(Transaction.id)).where(*base_filter)
        )
        tx_count = count_result.scalar() or 0

        return {
            "total_income": total_income,
            "total_expense": total_expense,
            "net_profit": total_income - total_expense,
            "transaction_count": tx_count,
            "expense_by_category": expense_by_category,
            "income_by_category": income_by_category,
        }


async def get_all_subscribed_users(report_type: str = "weekly") -> list[User]:
    async with async_session() as session:
        if report_type == "weekly":
            stmt = select(User).where(User.weekly_report == True)  # noqa: E712
        else:
            stmt = select(User).where(User.monthly_report == True)  # noqa: E712
        result = await session.execute(stmt)
        return list(result.scalars().all())
