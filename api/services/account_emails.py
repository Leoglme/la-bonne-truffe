"""The French emails of the account, in the voice of the app: today, the password reset link."""

from html import escape

from services.email_service import EmailMessage


class AccountEmails:
    """Writes the account emails: a plain text body, and an HTML body in the colours of the app."""

    @staticmethod
    def password_reset(to_email: str, name: str, link: str, expires_in_minutes: int) -> EmailMessage:
        """
        The email of « Mot de passe oublié ».

        Args:
            to_email: Address of the account.
            name: First name of the account, for the greeting.
            link: Link that opens the « Nouveau mot de passe » screen.
            expires_in_minutes: Lifetime of the link.

        Returns:
            The message.
        """
        subject = "Ton lien pour changer de mot de passe"
        text = (
            f"Bonjour {name},\n\n"
            "Pour choisir un nouveau mot de passe sur La Bonne Truffe, ouvre ce lien. "
            f"Il reste valable {expires_in_minutes} minutes et ne sert qu'une fois :\n"
            f"{link}\n\n"
            "Si tu n'as rien demandé, ignore ce message : ton mot de passe ne change pas.\n\n"
            "La Bonne Truffe"
        )
        html = (
            '<div style="background:#FBF6EE;padding:32px 16px;font-family:Nunito,Arial,sans-serif;color:#2B2420">'
            '<div style="max-width:480px;margin:0 auto;background:#FFFFFF;border-radius:24px;padding:28px">'
            '<p style="margin:0 0 20px 0;font-size:20px;font-weight:700">La Bonne Truffe</p>'
            f'<p style="margin:0 0 12px 0;font-size:16px">Bonjour {escape(name)},</p>'
            '<p style="margin:0 0 24px 0;font-size:16px;line-height:1.5">'
            "Pour choisir un nouveau mot de passe, ouvre ce lien. "
            f"Il reste valable {expires_in_minutes} minutes et ne sert qu'une fois.</p>"
            f'<a href="{escape(link)}" style="display:inline-block;padding:16px 28px;border-radius:999px;'
            'background:#E2552F;color:#FFFFFF;font-size:18px;font-weight:800;text-decoration:none">'
            "Choisir un nouveau mot de passe</a>"
            '<p style="margin:24px 0 0 0;font-size:14px;line-height:1.5;color:#7A6657">'
            "Si tu n'as rien demandé, ignore ce message : ton mot de passe ne change pas.</p>"
            "</div></div>"
        )
        return EmailMessage(to_email=to_email, subject=subject, text=text, html=html)
