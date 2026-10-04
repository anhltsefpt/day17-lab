"""Bước 7: Demo verifier + rollback.

Kịch bản A: một lệnh DELETE sai được chạy -> verifier phát hiện -> time travel khôi phục được.
Kịch bản B: lệnh DELETE sai, rồi VACUUM RETAIN 0 -> lịch sử mất -> KHÔNG khôi phục được.

Cách chạy:  python rollback_demo.py
"""
from setup_db import execute, history_versions, new_db, restore, snapshot, verify

BAD_SQL = "DELETE FROM dev_orders WHERE amount > 0"  # lệnh sai: xóa gần hết bảng


def count(con):
    return con.execute("SELECT COUNT(*) FROM dev_orders").fetchone()[0]


def scenario(title, vacuum_after):
    print(f"\n=== {title} ===")
    con = new_db()
    before = snapshot(con)
    print(f"1. Ban đầu: dev_orders có {count(con)} dòng, {len(history_versions(con, 'dev_orders'))} phiên bản lịch sử")

    execute(con, BAD_SQL)
    print(f"2. Chạy lệnh sai: {BAD_SQL}  ->  còn {count(con)} dòng")

    if vacuum_after:
        execute(con, "VACUUM dev_orders RETAIN 0 HOURS")
        print(f"3. Agent chạy tiếp: VACUUM dev_orders RETAIN 0 HOURS  ->  còn {len(history_versions(con, 'dev_orders'))} phiên bản lịch sử")

    damage = verify(before, snapshot(con))
    print(f"4. Verifier phát hiện: {damage}")

    ok = restore(con, "dev_orders")
    damage_after = verify(before, snapshot(con))
    if ok and not damage_after:
        print(f"5. Rollback THÀNH CÔNG: dev_orders có lại {count(con)} dòng, verifier không còn báo lỗi")
    else:
        print(f"5. Rollback THẤT BẠI: không còn phiên bản lịch sử. dev_orders chỉ còn {count(con)} dòng")


if __name__ == "__main__":
    scenario("Kịch bản A: DELETE sai, còn lịch sử", vacuum_after=False)
    scenario("Kịch bản B: DELETE sai, rồi VACUUM RETAIN 0", vacuum_after=True)
    print("\nKết luận: DELETE sai là lỗi rollback được (nên HỎI DUYỆT); VACUUM retention ngắn làm mất hẳn lịch sử (nên CHẶN).")
