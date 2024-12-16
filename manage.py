import click

from mike_action_provider.app import create_app


@click.group()
def cli():
    pass


def _list_routes(app):
    output = []
    for rule in app.url_map.iter_rules():
        methods = ','.join(rule.methods)
        output.append(f'{rule.endpoint} {methods} {rule.rule}')
    return output


@cli.command()
def list_routes():

    app = create_app()
    with app.test_request_context():
        routes = _list_routes(app)
        for route in routes:
            click.echo(route)


if __name__ == '__main__':
    cli()
