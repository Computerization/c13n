---
title: "数据库事务基础"
author: "马浩琨"
date: "Feb 22, 2026"
description: "数据库事务 ACID 特性、隔离级别与高并发实践指南"
latex: true
pdf: true
---

想象你在电商平台下单时，库存扣减成功了，但积分增加和支付扣款却同时失败，导致库存超卖，用户却没有得到积分，这无疑是一场灾难。这种场景在缺少事务保护的多用户、高并发环境下屡见不鲜。数据库事务（Transaction）正是为此而生，它是数据库操作的最小逻辑单元，确保一组操作要么全部成功，要么全部失败。事务的核心特性是原子性（Atomicity）、一致性（Consistency）、隔离性（Isolation）和持久性（Durability），简称 ACID。这些属性保障了数据在复杂环境下的可靠性，尤其在银行转账或订单处理等场景中不可或缺。本文将从事务基础入手，逐步深入隔离级别、实现实践和高性能优化，帮助你从入门到熟练应用事务，避免常见坑阱。阅读后，你将掌握事务原理，并在项目中自信使用。

## 事务基础概念

数据库事务是指一组不可分割的数据库操作序列，这些操作作为一个整体被执行，要么全部成功，要么全部失败。事务的生命周期通常从 BEGIN TRANSACTION 开始，执行一系列 SQL 语句，然后通过 COMMIT 提交或 ROLLBACK 回滚。以一个简单的转账为例，伪代码可以这样表示：BEGIN TRANSACTION；UPDATE account_a SET balance = balance - 100 WHERE id = 1；UPDATE account_b SET balance = balance + 100 WHERE id = 2；COMMIT；如果中间任何一步失败，整个事务都会回滚，确保账户余额一致。这与单条 SQL 语句不同，后者默认是自动提交的原子单元，而事务允许批量操作，提供更强的控制力。

ACID 属性是事务的基石。原子性保证事务内所有操作作为一个不可分割的单元执行，比如转账场景中扣款和入账必须同时成功，否则全部撤销，避免部分失败导致数据不一致。一致性确保事务执行前后数据库从一个一致状态转移到另一个一致状态，例如转账后总余额不变，且余额始终不低于零，如果违反业务约束如余额负值，事务会自动回滚。隔离性防止并发事务相互干扰，避免脏读或幻读等现象，确保每个事务仿佛独占数据库。持久性则承诺一旦事务提交，变更将永久保存，即使系统崩溃也能通过日志恢复。

事务日志在保障 ACID 中扮演关键角色，特别是通过 WAL（Write-Ahead Logging，先写日志）机制。在事务执行过程中，所有变更先记录到日志文件中，只有在 COMMIT 时才更新实际数据页。这种设计确保了持久性：即使崩溃，数据库能从日志重放已提交事务，并回滚未提交的变更。以 MySQL InnoDB 为例，一个简单的事务日志记录可能包括事务 ID、变更的旧值和新值，以及 LSN（Log Sequence Number）用于顺序恢复。这不仅提升了性能，还支持崩溃恢复和复制。

为了直观理解事务执行，以下是 MySQL 中的简单 SQL 示例，展示转账事务：

```sql
START TRANSACTION;
UPDATE accounts SET balance = balance - 100 WHERE id = 1;
UPDATE accounts SET balance = balance + 100 WHERE id = 2;
COMMIT;
```

这段代码首先启动事务，然后从账户 1 扣除 100 元，并向账户 2 增加 100 元，最后提交。如果第二条 UPDATE 因余额不足失败，整个事务会回滚，第一条 UPDATE 的变更也会撤销，确保原子性。注意，InnoDB 默认使用行级锁，仅锁定受影响的行，避免全局阻塞。

## 事务隔离级别

并发事务可能引发多种问题，首先是脏读，即事务 A 修改数据但未提交，事务 B 读取到这些未确认变更，如果 A 回滚，B 就读到了「脏」数据。以两人同时转账场景为例，事务 A 扣款后未提交，B 读取余额导致错误决策。其次是不可重复读，同一事务内多次读取同一数据却得到不同结果，因为其他事务在间隙中提交了变更。最后是幻读，范围查询如 SELECT * FROM orders WHERE amount > 100 时，结果集因其他事务插入新行而「幻觉」变化。

数据库定义了四种隔离级别来平衡一致性和性能，从低到高依次是 READ UNCOMMITTED、READ COMMITTED、REPEATABLE READ 和 SERIALIZABLE。READ UNCOMMITTED 不解决任何问题，允许脏读等，性能最高但仅适合测试。READ COMMITTED 通过提交时读解决脏读，但仍存在不可重复读和幻读，适用于读多写少场景。REPEATABLE READ 是 MySQL 默认级别，解决脏读和不可重复读，通过 MVCC（多版本并发控制）实现，但可能有幻读，适合多数 OLTP 应用。SERIALIZABLE 解决所有问题，使用串行化锁，但性能最低，仅用于高一致性需求。

设置隔离级别在 SQL 中非常直接，例如在 MySQL 中使用 SET TRANSACTION ISOLATION LEVEL REPEATABLE READ；而在 PostgreSQL 中是 SET SESSION CHARACTERISTICS AS TRANSACTION ISOLATION LEVEL REPEATABLE READ；。这些命令影响当前会话或全局。底层依赖锁机制：行锁锁定单行，表锁锁定整表，MySQL 的间隙锁则针对索引范围防止幻读插入。

以下是演示不可重复读的 MySQL 示例，两事务并发执行：

```sql
-- 会话 1
SET TRANSACTION ISOLATION LEVEL READ COMMITTED;
START TRANSACTION;
SELECT balance FROM accounts WHERE id = 1;  -- 读取到 1000
-- 等待会话 2

-- 会话 2
START TRANSACTION;
UPDATE accounts SET balance = 900 WHERE id = 1;
COMMIT;  -- 提交变更

-- 会话 1 继续
SELECT balance FROM accounts WHERE id = 1;  -- 现在读取到 900，不可重复读
COMMIT;
```

这段代码在 READ COMMITTED 下，会话 1 两次 SELECT 结果不同，因为会话 2 在间隙提交了 UPDATE。解读时注意，READ COMMITTED 每次读最新提交版本，但不锁定读行，导致间隙变更。如果提升到 REPEATABLE READ，MySQL 通过 MVCC 为第一次读创建快照，后续读使用同一快照，避免不可重复读。实际测试时，可用两个终端模拟并发，观察差异。

## 事务实现与最佳实践

主流数据库广泛支持事务，MySQL 的 InnoDB 引擎提供完整 ACID，通过 MVCC 和两阶段锁实现高并发；PostgreSQL 以强一致性著称，支持 SAVEPOINT 和高级锁；Oracle 和 SQL Server 则在企业级场景中通过 XA 协议处理分布式事务。这些实现虽有差异，但核心依赖日志和锁。

在编程语言中，事务通过框架简化。Java 的 Spring 使用 @Transactional 注解自动管理：

```java
@Service
public class OrderService {
    @Transactional(isolation = Isolation.REPEATABLE_READ)
    public void processOrder(Order order) {
        // 扣减库存
        inventoryRepository.decrease(order.getItemId(), order.getQuantity());
        // 增加积分
        userRepository.addPoints(order.getUserId(), order.getPoints());
        // 记录订单
        orderRepository.save(order);
    }
}
```

这段 Java 代码在 processOrder 方法上应用 REPEATABLE READ 隔离，如果任何仓库操作失败，整个方法回滚。解读关键：@Transactional 拦截方法调用，启动事务，异常时回滚；isolation 参数自定义级别，避免默认宣传读。需注意嵌套事务时使用 REQUIRES_NEW 传播行为。

Python 的 SQLAlchemy 类似，使用 session 上下文：

```python
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine

engine = create_engine('mysql://user:pass@localhost/db')
Session = sessionmaker(bind=engine)

def process_order(session, order):
    try:
        session.query(Inventory).filter_by(item_id=order.item_id)\
                               .update({Inventory.quantity: Inventory.quantity - order.quantity})
        session.commit()
    except:
        session.rollback()
        raise

session = Session()
process_order(session, order)
```

这里显式使用 try-except 管理提交和回滚，session 作为事务边界。解读时，update 是原子操作，但批量需在事务内；异常捕获确保回滚，防止数据不一致。

最佳实践强调保持事务简短，避免长事务锁等待，可通过分拆或设置锁超时解决，如 MySQL 的 innodb_lock_wait_timeout。显式 COMMIT/ROLLBACK 优于隐式，嵌套事务用 SAVEPOINT 如 SAVEPOINT sp1; ROLLBACK TO sp1;。读写分离时，主库写从库读需注意一致性，分布式场景用 2PC 或 Seata。避免死锁的关键是统一锁顺序，如总是按 ID 升序加锁。性能优化依赖索引，使用 EXPLAIN ANALYZE 查询计划；批量操作如 INSERT ... VALUES (多行) 减少日志；连接池如 HikariCP 复用连接。监控用 SHOW ENGINE INNODB STATUS 查看锁和事务状态。

## 高级话题与扩展

分布式事务引入 CAP 理论挑战，放弃强一致性换取可用性，常见模式如 TCC（Try-Confirm-Cancel）或 SAGA（长事务拆分为本地事务 + 补偿）。NoSQL 如 MongoDB 支持多文档 ACID 事务，但 Cassandra 更偏最终一致性。未来 NewSQL 如 TiDB 融合分布式和高 ACID，提供 HTAP 能力。


事务的核心是 ACID 属性和隔离级别选择，实践要点包括短事务、锁优化和框架集成。这些确保数据在并发下的可靠性。你的收获包括：掌握四隔离级别及并发问题；编写安全事务代码；识别并优化死锁陷阱。现在，在本地 MySQL 实验上述示例，测试隔离差异。你的项目中遇到过事务问题吗？欢迎评论分享经验。参考《数据库系统概念》、MySQL 官方文档和 DB Fiddle 在线工具深入实践。
