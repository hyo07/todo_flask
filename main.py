from flask import Flask, render_template, request, redirect, url_for
import sqlite3

app = Flask(__name__)

sql_path = "./db/todo.db"
en_ja = {"no": "未実行", "run": "実行中", "end": "完了"}
ja_en = {"未実行": "no", "実行中": "run", "完了": "end"}


# DBにコネクション
def get_db_connection():
    connection = sqlite3.connect(sql_path)
    connection.row_factory = sqlite3.Row
    return connection


@app.route("/")
def index():
    connection = get_db_connection()
    cursor = connection.cursor()
    res = cursor.execute("SELECT * FROM todo")
    res_list = res.fetchall()
    # 新しいものが上に来るように、リストを逆順に変換
    res_list_rev = res_list[::-1]

    todo = {}
    # ページ数受け取り
    res_todo = request.args.get("page", 1)
    todo["page"] = int(res_todo)
    # 前のページと次のページの生成
    if todo["page"] > 1:
        todo["previous_page"] = todo["page"] - 1
    if todo["page"] * 10 < len(res_list):
        todo["next_page"] = todo["page"] + 1
    # 現在のページの先頭のインデントを確認
    start_num = (todo["page"] - 1) * 10
    # DBから受け取ったリストをスライスで区切る
    todo["now_page_data"] = res_list_rev[start_num:(start_num + 10)]

    return render_template("index.html", todo=todo)


# タスク追加
@app.route("/add", methods=["GET", "POST"])
def add():
    # タスク追加ページに飛ばす
    if request.method == "GET":
        todo = {}
        return render_template("edit.html", type="add", todo=todo)

    # エラーの設定
    else:
        error = []
        if not request.form["name"]:
            error.append("タスク名を入力してください")
        if not request.form["duedate"]:
            error.append("期限を入力してください")

        # エラー処理
        if error:
            todo = request.form.to_dict()
            return render_template("edit.html", type="add", todo=todo, error_list=error)

        # 追加のためのデータやりとり
        if request.form.get("status", "no") == "no":
            status = "未実行"
        elif request.form.get("status", "no") == "run":
            status = "実行中"

        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute("""INSERT INTO todo (name, duedate, status, memo)VALUES (?, ?, ?, ?)""",
                       (request.form["name"], request.form["duedate"], status, request.form["memo"]))
        connection.commit()
        return redirect(url_for("index"))


# 削除確認ページに飛ぶ
@app.route("/delcheck/<int:id>", methods=["GET", "POST"])
def delcheck(id):
    if request.method == "GET":
        connection = get_db_connection()
        cursor = connection.cursor()
        res = cursor.execute("SELECT * FROM todo WHERE id = ?", (id,))
        return render_template("delete.html", res=res.fetchone(), id=id)


# 削除を実行
@app.route("/delete/<int:id>", methods=["GET", "POST"])
def delete(id):
    if request.method == "GET":
        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute("DELETE FROM todo WHERE id = ?", (id,))
        connection.commit()
        return redirect(url_for("index"))


@app.route("/edit/<int:id>")
def edit(id):
    status_list = ["no", "run", "end"]
    connection = get_db_connection()
    cursor = connection.cursor()
    res = cursor.execute("SELECT * FROM todo WHERE id = ?", (id,))
    res = res.fetchone()
    # DBに日本語表記で保存されたstatusを、英語に変換
    res_status = ja_en[res["status"]]
    # リストから抜き、先頭に追加することでソートを行う
    status_list.remove(res_status)
    status_list.insert(0, res_status)

    return render_template("edit.html", type="edit", todo=res, status_list=status_list, en_ja=en_ja)


# タスク更新
@app.route("/update/<int:id>", methods=["POST"])
def update(id):
    error = []
    if not request.form["name"]:
        error.append("タスク名を入力してください")
    if not request.form["duedate"]:
        error.append("期限を入力してください")

    if error:
        todo = request.form.to_dict()
        todo["id"] = id
        return render_template("edit.html", type="edit", todo=todo, error_list=error)

    if request.form.get("status", "no") == "no":
        status = "未実行"
    elif request.form.get("status", "no") == "run":
        status = "実行中"
    elif request.form.get("status", "no") == "end":
        status = "完了"

    connection = get_db_connection()
    cursor = connection.cursor()
    cursor.execute("UPDATE todo set name = ?, duedate = ?, status = ?, memo = ? WHERE id = ?",
                   (request.form["name"],
                    request.form["duedate"],
                    status,
                    request.form["memo"],
                    id))
    connection.commit()
    return redirect(url_for("index"))


if __name__ == "__main__":
    app.run()
