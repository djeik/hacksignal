from app import app

import psycopg2

class RealDatabase:
    ticket_data_columns = ['ticketId', 'ticketContents', 'ticketTableNumber',
                'ticketStatusName', 'ticketMentorData', 'userId', 'userName',
                'userEmail']

    @staticmethod
    def get_connection():
        return psycopg2.connect(
                "dbname='%s' user='%s' password='%s' host='%s'" %
                tuple(app.config['DATABASE'][k]
                    for k in ['name', 'user', 'password', 'host']))

    @staticmethod
    def list_tickets(selector):
        conn = Database.get_connection()
        cur = conn.cursor()

        columns = ', '.join(Database.ticket_data_columns)

        if selector == "all":
            # then select all tickets
            cur.execute(
                    "SELECT " + columns + " FROM Ticket "
                    "NATURAL JOIN Hacker NATURAL JOIN TicketStatus ORDER BY ticketStatusId;")
        elif selector == "open":
            # then select all non-closed tickets
            cur.execute(
                    "SELECT " + columns + " FROM Ticket "
                    "NATURAL JOIN Hacker "
                    "NATURAL JOIN TicketStatus "
                    "WHERE ticketStatusName!='closed' "
                    "ORDER BY ticketStatusId;")
        else:
            # then try to look up the given selector
            cur.execute(
                    "SELECT * FROM TicketStatus WHERE ticketStatusName=%s;",
                    (selector,))

            # if it does not exist
            if not cur.rowcount:
                raise ValueError(" no such ticket status '%s'." % selector)
                #return jsonify( {
                #    "status": "failed",
                #    "message": "no such ticket status '%s'." % ticket_type
                #} )

            # get the tickets of that kind
            cur.execute(
                    "SELECT " + columns + " FROM Ticket "
                    "NATURAL JOIN Hacker NATURAL JOIN TicketStatus "
                    "WHERE ticketStatusName=%s "
                    "ORDER BY ticketStatusId;", (selector,))

        records = [dict(zip(Database.ticket_data_columns, r))
                for r in cur.fetchall()]
        conn.close()
        return records

    @staticmethod
    def get_ticket(ticket_id):
        columns = ', '.join(Database.ticket_data_columns)

        with Database.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT " + columns + " FROM Ticket "
                    "NATURAL JOIN Hacker NATURAL JOIN TicketStatus "
                    "WHERE ticketId=%s;", (ticket_id,))
            return dict(zip(Database.ticket_data_columns, cur.fetchone()))

    @staticmethod
    def create_user_if_not_exists(name, email):
        """ Returns the id of the user. Raises a ValueError if the user
            already exists and the names don't match! """
        conn = Database.get_connection()
        cur = conn.cursor()
        cur.execute("SELECT userId, userName FROM Hacker WHERE userEmail=%s;",
                (email,))
        if not cur.rowcount: # if the user doesn't exist
            # create them
            cur.execute("INSERT INTO hacker ( userName, userEmail ) "
                    "VALUES ( %s, %s );",
                    (name, email))
            cur.execute("SELECT LASTVAL();")
            user_id = cur.fetchone()
            cur.execute("SELECT userId, userName FROM Hacker WHERE userId=%s;",
                    (user_id,))

            conn.commit()

        # fetch the record that was either selected or inserted
        record = cur.fetchone()
        # check that the names match
        if name != record[1]:
            raise ValueError("The given name '%s' does not match the one "
                    "already associated with that email address, '%s'." %
                    (name, record[1]))

        return record[0] # return the userId

    @staticmethod
    def create_ticket(user_id, ticket_table_number, ticket_contents,
            ticket_status_name):
        """ Create a ticket. """
        conn = Database.get_connection()
        cur = conn.cursor()
        cur.execute("SELECT ticketStatusId FROM TicketStatus "
                "WHERE ticketStatusName=%s;",
                (ticket_status_name,))
        if not cur.rowcount:
            raise ValueError('invalid ticket status name')

        (ticket_status_id,) = cur.fetchone()
        cur.execute("INSERT INTO Ticket "
                "( userId, ticketTableNumber, ticketContents, ticketStatusId ) "
                "VALUES ( %s, %s, %s, %s ) RETURNING ticketId;",
                (user_id, ticket_table_number, ticket_contents,
                    ticket_status_id))
        conn.commit()
        (ticket_id,) = cur.fetchone()
        return Database.get_ticket(ticket_id)

    @staticmethod
    def update_ticket_status(ticket_id, ticket_status_name=None,
            ticket_status_id=None):
        if ticket_status_name is not None and ticket_status_id is not None:
            raise ValueError("both ticketStatusName and ticketStatusId "
                    "specified as ticket update criteria")
        with Database.get_connection() as conn:
            cur = conn.cursor()
            if ticket_status_name is not None:
                cur.execute("SELECT ticketStatusId FROM TicketStatus "
                        "WHERE ticketStatusName=%s;",
                        (ticket_status_name,))
                if not cur.rowcount:
                    raise ValueError("invalid ticket status name %s" %
                            (ticket_status_name,))
                ticket_status_id = cur.fetchone()
                cur.execute("UPDATE Ticket SET ( ticketStatusId ) = ( %s ) "
                        "WHERE ticketId=%s;",
                        (ticket_status_id, ticket_id))
            elif ticket_status_id is not None:
                cur.execute("UPDATE Ticket SET ( ticketStatusId ) = ( %s ) "
                        "WHERE ticketId=%s;",
                        (ticket_status_id, ticket_id))
            else:
                raise ValueError("neither ticketStatusName nor ticketStatusId "
                        "specified as ticket udpate criteria")

    @staticmethod
    def update_ticket_data(ticket_id, ticket_data):
        with Database.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("UPDATE Ticket SET ( ticketMentorData ) = ( %s ) "
                    "WHERE ticketId=%s;", (ticket_data, ticket_id))

    @staticmethod
    def delete_ticket(ticket_id):
        with Database.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("DELETE FROM Ticket WHERE ticketId=%s;", (ticket_id,))

    @staticmethod
    def delete_user(user_email=None, user_id=None):
        """ Delete a user from the database, deleting all their associated
            tickets. Deletion can be done by id or by email address, since both
            uniquely identify a single user.
        """
        with Database.get_connection() as conn:
            cur = conn.cursor()
            if user_email is not None:
                cur.execute("DELETE FROM User WHERE userEmail=%s;",
                        (user_email,))
            elif user_id is not None:
                cur.execute("DELETE FROM User WHERE userId=%s;",
                        (user_id,))
            else:
                raise TypeError("no criteria specified for account deletion")

    @staticmethod
    def get_ticket_status_names():
        with Database.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT ticketStatusName FROM TicketStatus;")
            return [r[0] for r in cur.fetchall()]

class FakeDatabase:
    @staticmethod
    def list_tickets(selector):
        return [ {
            'ticketId': 1,
            'ticketContents': 'fake ticket',
            'ticketTableNumber': 1337,
            'ticketStatusName': 'pending',
            'ticketMentorData': 'awesome mentorship dude',
            'userId': 1,
            'userName': 'SuperCool McBro',
            'userEmail': 'supercool.mcbro@webscale.website'
        } ]

    @staticmethod
    def get_ticket(ticket_id):
        if ticket_id == 1:
            return {
                'ticketId': 1,
                'ticketContents': 'fake ticket',
                'ticketTableNumber': 1337,
                'ticketStatusName': 'pending',
                'ticketMentorData': 'awesome mentorship dude',
                'userId': 1,
                'userName': 'SuperCool McBro',
                'userEmail': 'supercool.mcbro@webscale.website'
            }
        else:
            return None

    @staticmethod
    def create_user_if_not_exists(name, email):
        return 1

    @staticmethod
    def create_ticket(user_id, ticket_table_number, ticket_contents,
            ticket_status_name):
        return {
            'ticketId': 1,
            'ticketContents': ticket_contents,
            'ticketTableNumber': ticket_table_number,
            'ticketStatusName': ticket_status_name,
            'ticketMentorData': 'awesome mentorship dude',
            'userId': user_id,
            'userName': 'SuperCool McBro',
            'userEmail': 'supercool.mcbro@webscale.website'
        }

    @staticmethod
    def update_ticket_status(ticket_id, ticket_status_name=None,
            ticket_status_id=None):
        return None

    @staticmethod
    def update_ticket_data(ticket_id, ticket_data):
        return None

    @staticmethod
    def delete_ticket(ticket_id):
        return None

    @staticmethod
    def delete_user(user_email=None, user_id=None):
        return None

    @staticmethod
    def get_ticket_status_names():
        return ['pending', 'confirmed', 'sent', 'closed']

if app.config['DATABASE']['active']:
    Database = RealDatabase
else:
    Database = FakeDatabase
